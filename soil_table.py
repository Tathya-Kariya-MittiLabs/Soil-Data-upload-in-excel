#streamlit run soil_table.py
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
import os

# Initialize session state
if "table_data" not in st.session_state:
    st.session_state["table_data"] = pd.DataFrame(
        columns=["Pedon", "Horizon", "Depth (cm)", "Loc X", "Loc Y", "Sand (%)",
                 "Silt (%)", "Clay (%)", "Bulk Density", "Particle Density Mgm^-3",
                 "Pore Space (%)", "Percent Moisture Retention (Mpa)",
                 "Available Water (%)", "Hydraulic Conductivity (cm hr^-1)"]
    ).astype({
        "Pedon": str,
        "Horizon": str,
        "Depth (cm)": str,
        "Loc X": float,
        "Loc Y": float,
        "Sand (%)": float,
        "Silt (%)": float,
        "Clay (%)": float,
        "Bulk Density": float,
        "Particle Density Mgm^-3": float,
        "Pore Space (%)": float,
        "Percent Moisture Retention (Mpa)": float,
        "Available Water (%)": float,
        "Hydraulic Conductivity (cm hr^-1)": float,
    })

# Load or create Excel file
def load_or_create_excel():
    file_path = "external_data_2.xlsx"
    if not os.path.exists(file_path):
        st.session_state["table_data"].to_excel(file_path, index=False)
    else:
        loaded_data = pd.read_excel(file_path)
        # Align columns with session state DataFrame
        for col in st.session_state["table_data"].columns:
            if col not in loaded_data.columns:
                loaded_data[col] = "" if st.session_state["table_data"][col].dtype == "object" else float('nan')
        st.session_state["table_data"] = loaded_data.astype(st.session_state["table_data"].dtypes)
    return st.session_state["table_data"]

# Save updated data to Excel
def save_data_to_excel():
    file_path = "external_data_2.xlsx"
    try:
        st.session_state["table_data"].dropna(how="all").to_excel(file_path, index=False)
        st.success("Data saved successfully!")
    except PermissionError:
        st.error("Permission denied: Ensure the file is not open elsewhere.")

# Refresh data in the editable table
def refresh_data():
    load_or_create_excel()

#######################################
def load_excel_or_csv_files_separately(file_paths, file_columns_mapping):
    file_dfs = {}
    for file_path in file_paths:
        file_extension = os.path.splitext(file_path)[-1].lower()

        lat_col = file_columns_mapping[file_path]['lat_col']
        lon_col = file_columns_mapping[file_path]['lon_col']

        if file_extension == '.xlsx':
            df = pd.read_excel(file_path, keep_default_na=False)
        else:
            st.error(f"File format not supported: {file_path}")
            continue

        if lat_col not in df.columns or lon_col not in df.columns:
            st.error(f"Latitude/Longitude columns not found in file: {file_path}")
            continue

        df = df.rename(columns={lat_col: 'x', lon_col: 'y'})
        file_dfs[file_path] = df

    return file_dfs

def create_map(data):
    coords = data[["Loc X", "Loc Y"]].drop_duplicates().dropna().to_dict(orient="records")
    if not coords:
        st.error("No valid coordinates found!")
        return None

    map_center = (data["Loc X"].mean(), data["Loc Y"].mean())
    m = folium.Map(location=map_center, zoom_start=5)

    for _, row in data.iterrows():
        if pd.notnull(row["Loc X"]) and pd.notnull(row["Loc Y"]):
            # Prepare the popup content
            popup_content = "<br>".join([f"<b>{key}</b>: {value}" for key, value in row.drop(["Loc X", "Loc Y"]).items() if pd.notnull(value)])
            popup = folium.Popup(popup_content, max_width=300)

            # Create a custom marker with a 'O' icon
            marker_icon = folium.DivIcon(html=f"""<div style="font-size: 20px; font-weight: bold; color: black;">O</div>""")

            # Add the marker to the map
            folium.Marker(
                location=(row['Loc X'], row['Loc Y']),
                tooltip=f"{row['Loc X']} , {row['Loc Y']}",
                popup=popup,
                icon=marker_icon  # Apply the custom 'O' icon with adjusted size
            ).add_to(m)

    return m


# Load initial data
load_or_create_excel()

# Editable table
st.title("Soil Data Management")
st.markdown("### Editable Table")
edited_table_data = st.data_editor(
    st.session_state["table_data"],
    num_rows="dynamic",
    use_container_width=True,
    key="table_editor"
)

# Update the session state table data with edited data
st.session_state["table_data"] = edited_table_data


# Add column functionality
st.markdown("### Add Column")
new_column_name = st.text_input("Enter new column name:")
if st.button("Add Column"):
    if new_column_name and new_column_name not in st.session_state["table_data"].columns:
        st.session_state["table_data"][new_column_name] = pd.NA  # Initialize with NaN
        st.rerun()  # Refresh the app to display the new column
    elif new_column_name in st.session_state["table_data"].columns:
        st.warning(f"Column '{new_column_name}' already exists!")
    else:
        st.warning("Column name cannot be empty.")


# Buttons for saving and refreshing data
col1, col2 = st.columns(2)
with col1:
    if st.button("Save Data"):
        save_data_to_excel()

with col2:
    if st.button("Refresh Data"):
        refresh_data()

# Display map
st.markdown("### Map")
map_placeholder = st.empty()
map_obj = create_map(st.session_state["table_data"])
if map_obj:
    with map_placeholder:
        folium_static(map_obj, width=800, height=600)

