import streamlit as st
import pandas as pd
import math
import numpy as np
from PIL import Image  # Added for logo display

# --- Load Logo ---
logo = Image.open("assets/logo.png")
st.image(logo, width=150)  # Display at top of the app

# --- CONFIGURATION & STYLING ---
st.set_page_config(page_title="Forestry Volume Calculator", layout="centered")

st.markdown("""
    <style>
    .main {
        background-color: #f5f7f9;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #2e7d32;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

# --- CONSTANTS & DATA ---
SPECIES_DATA = {
    "Chir Pine": {"f": 0.45, "a": 35.0, "b": 0.035, "c": 1.1},
    "Blue Pine": {"f": 0.46, "a": 38.0, "b": 0.032, "c": 1.2},
    "Deodar": {"f": 0.50, "a": 40.0, "b": 0.030, "c": 1.2},
    "Fir/Spruce": {"f": 0.47, "a": 42.0, "b": 0.028, "c": 1.3},
    "Oak": {"f": 0.48, "a": 25.0, "b": 0.040, "c": 1.0},
    "Wild Olive": {"f": 0.42, "a": 15.0, "b": 0.050, "c": 0.9}
}

M3_TO_CFT = 35.3147

# --- FUNCTIONS ---
def estimate_height(species, dbh):
    """
    Chapman-Richards Model: H = 1.3 + a * (1 - exp(-b * DBH))^c
    (Constants 'a, b, c' are placeholders based on typical species growth)
    """
    params = SPECIES_DATA[species]
    a, b, c = params['a'], params['b'], params['c']
    h = 1.3 + a * (1 - np.exp(-b * dbh))**c
    return round(h, 2)

def calculate_volume(dbh_cm, height_m, form_factor):
    dbh_m = dbh_cm / 100
    volume_m3 = (math.pi / 4) * (dbh_m**2) * height_m * form_factor
    return volume_m3

# --- UI LAYOUT ---
st.title("Standing Tree Volume Calculator")
st.write("Professional tool for field inventory and stand estimation.")

with st.form("calc_form"):
    st.subheader("Tree Parameters")
    
    col1, col2 = st.columns(2)
    
    with col1:
        species = st.selectbox("Select Species", list(SPECIES_DATA.keys()))
        dbh = st.number_input("DBH (Diameter at Breast Height) in cm", min_value=1.0, step=1.0, help="Measured at 1.3m height")
        
    with col2:
        height_input = st.number_input("Height in meters (Optional)", min_value=0.0, step=0.5, help="Leave 0 to estimate based on DBH")
        tree_count = st.number_input("Number of Trees", min_value=1, value=1, step=1)

    submitted = st.form_submit_button("Calculate Volume")

# --- LOGIC & OUTPUT ---
if submitted:
    if dbh <= 0:
        st.error("Please enter a valid DBH value.")
    else:
        # Determine Height
        is_estimated = False
        if height_input == 0:
            final_height = estimate_height(species, dbh)
            is_estimated = True
        else:
            final_height = height_input

        # Get Form Factor
        f = SPECIES_DATA[species]['f']
        
        # Calculate
        vol_tree_m3 = calculate_volume(dbh, final_height, f)
        vol_tree_cft = vol_tree_m3 * M3_TO_CFT
        
        total_vol_m3 = vol_tree_m3 * tree_count
        total_vol_cft = vol_tree_cft * tree_count

        # Display Metrics
        st.success(f"Calculation Complete {'(Height Estimated)' if is_estimated else ''}")
        
        m1, m2 = st.columns(2)
        m1.metric("Vol per Tree (m³)", f"{vol_tree_m3:.3f}")
        m2.metric("Vol per Tree (cft)", f"{vol_tree_cft:.2f}")
        
        m3, m4 = st.columns(2)
        m3.metric("Total Stand Vol (m³)", f"{total_vol_m3:.3f}")
        m4.metric("Total Stand Vol (cft)", f"{total_vol_cft:.2f}")

        # Data for Export
        result_data = {
            "Species": [species],
            "DBH (cm)": [dbh],
            "Height (m)": [final_height],
            "Height Type": ["Estimated" if is_estimated else "Measured"],
            "Form Factor": [f],
            "Tree Count": [tree_count],
            "Vol/Tree (m3)": [round(vol_tree_m3, 4)],
            "Total Vol (m3)": [round(total_vol_m3, 4)],
            "Total Vol (cft)": [round(total_vol_cft, 2)]
        }
        df = pd.DataFrame(result_data)
        
        st.write("---")
        st.subheader("Summary Table")
        st.dataframe(df)

        # Export Options
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download Results as CSV (Excel)",
            data=csv,
            file_name=f"Forest_Volume_{species}.csv",
            mime='text/csv',
        )

# --- FOOTER ---
st.write("---")
st.caption("Note: Height estimation uses the Chapman-Richards model. Form factors (f) are based on standard species averages.")
