# # # streamlit run main_2.py
# streamlit run Soil_Data_Upload_Form_Into_Excel.py
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
import geopandas as gpd
import numpy as np
import os

# Load or create the external_data.xlsx file
def load_or_create_excel():
    file_path = 'external_data_2.xlsx'
    if not os.path.exists(file_path):
        df = pd.DataFrame(columns=['Pedon', 'Horizon', 'Depth (cm)', 'Loc X', 'Loc Y', 'Sand (%)', 'Slit (%)', 'Clay (%)', 
                                   'Bulk Density', 'Particle Density Mgm^-3', 'Pore Space (%)', 
                                   'Percent Moisture Retention (Mpa)', 'Available Water (%)', 
                                   'Hydraulic Conductivity (cm hr^-1)'])
        df.to_excel(file_path, index=False)
    else:
        df = pd.read_excel(file_path)
    return df

# Function to append new data to the Excel file
def append_to_excel(data):
    file_path = 'external_data_2.xlsx'
    df = pd.read_excel(file_path)
    df = pd.concat([df, pd.DataFrame([data])], ignore_index=True)
    df.to_excel(file_path, index=False)

# Function to load GeoJSON files
def load_geojson_files(geojson_paths):
    geojson_data = []
    for geojson_path in geojson_paths:
        if os.path.exists(geojson_path):
            gdf = gpd.read_file(geojson_path)
            geojson_data.append(gdf)
        else:
            st.error(f"GeoJSON file at {geojson_path} not found!")
    return geojson_data

# Load Excel or CSV files and create separate dataframes
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

# Function to refresh the Excel data
def refresh_data():
    st.session_state['excel_data'] = load_or_create_excel()

# Main function for displaying the map and handling the data
def main(geojson_paths, file_paths, file_columns_mapping):
    file_dfs = load_excel_or_csv_files_separately(file_paths, file_columns_mapping)

    coords = []
    for file_path, df in file_dfs.items():
        temp_df = df[['x', 'y']].drop_duplicates()
        coords.extend([{'x': row['x'], 'y': row['y'], 'source_file': file_path} for _, row in temp_df.iterrows()])

    if not coords:
        st.error("No valid coordinates found!")
        return None

    df['x'] = pd.to_numeric(df['x'], errors='coerce')
    df['y'] = pd.to_numeric(df['y'], errors='coerce')


    map_center = (np.mean([coord['x'] for coord in coords]), np.mean([coord['y'] for coord in coords]))
    m = folium.Map(location=map_center, zoom_start=5)

    geojson_data = load_geojson_files(geojson_paths)
    for gdf in geojson_data:
        folium.GeoJson(gdf).add_to(m)

    for coord in coords:
        # Get the appropriate DataFrame for the source file
        df = file_dfs[coord['source_file']]
        filtered_df = df[(df['x'] == coord['x']) & (df['y'] == coord['y'])]

        if not filtered_df.empty:
            # Display only the first few columns to avoid overcrowding the popup
            html = filtered_df.iloc[:, :filtered_df.shape[1]].to_html(classes="table table-striped table-hover table-condensed table-responsive")
            # popup = folium.Popup(html, max_width=1000)
            popup = folium.Popup(folium.IFrame(html, width=500, height=500), max_width=1000)

            # Define a custom marker with 'O' as the icon using DivIcon with smaller size
            marker_icon = folium.DivIcon(html=f"""<div style="font-size: 20px; font-weight: bold; color: black;">O</div>""")

            folium.Marker(
                location=(coord['x'], coord['y']),
                tooltip=f"{coord['x']} , {coord['y']}",
                popup=popup,
                icon=marker_icon  # Apply the custom 'O' icon with adjusted size
            ).add_to(m)

    return m

# Paths for the GeoJSON files
geojson_paths = ['india_district.geojson']

# Paths for the data files (Excel)
file_paths = ['external_data_2.xlsx']

# Create refresh button to reload external_data.xlsx
if st.button('Refresh Data'):
    refresh_data()

# Render the map
st.session_state['map'] = main(geojson_paths, file_paths, {'external_data_2.xlsx': {'lat_col': 'Loc X', 'lon_col': 'Loc Y'}})
folium_static(st.session_state['map'], width=800, height=600)

# Form for adding data
st.title("Add Soil Data")

with st.form(key='soil_data_form'):
    pedon = st.text_input("Pedon", key="pedon")
    horizon = st.text_input("Horizon [Format: H1,H2,H3...]", key="horizon")
    depth = st.text_input("Depth (cm) [Format: D1,D2,D3...]", key="depth")
    loc_X = st.number_input("Loc X", min_value=0, key="loc_X")
    loc_Y = st.number_input("Loc Y", min_value=0, key="loc_Y")
    sand = st.text_input("Sand (%) [Format: SA1,SA2,SA3...]", key="sand")
    slit = st.text_input("Slit (%) [Format: SL1,SL2,SL3...]", key="slit")
    clay = st.text_input("Clay (%) [Format: C1,C2,C3...]", key="clay")
    bulk_density = st.text_input("Bulk Density [Format: BD1,BD2,BD3...]", key="bulk_density")
    particle_density = st.text_input("Particle Density Mgm^-3 [Format: PD1,PD2,PD3...]", key="particle_density")
    pore_space = st.text_input("Pore Space (%) [Format: PS1,PS2,PS3...]", key="pore_space")
    moisture_retention = st.text_input("Percent Moisture Retention (Mpa) [Format: PMR1,PMR2,PMR3...]", key="moisture_retention")
    available_water1 = st.text_input("Available Water (%) [Format: AW1,AW2,AW3...]", key="available_water1")
    hydraulic_conductivity = st.text_input("Hydraulic Conductivity (cm hr^-1) [Format: HC1,HC2,HC3...]", key="hydraulic_conductivity")

    col_names = st.text_input("Additional Column Names (comma-separated) [CH = Column Heading |Format: CH1,CH2,CH3...]", key="col_names")
    col_values = st.text_input(f"Values for Additional Columns (comma-separated) [CH = Column Heading, V = Value|Format: (CH1_V1,CH1_V2,CH1_V3...),(CH2_V1,CH2_V2,CH2_V3...)]", key="col_values")

    submit_button = st.form_submit_button("Save")


import re

if submit_button:
    # Split the depth input
    depth_list = depth.split(',')
    
    # Initialize lists for other columns that might have multiple values
    horizon_list = horizon.split(',')
    sand_list = str(sand).split(',')
    slit_list = str(slit).split(',')
    clay_list = str(clay).split(',')
    bulk_density_list = str(bulk_density).split(',')
    particle_density_list = str(particle_density).split(',')
    pore_space_list = str(pore_space).split(',')
    moisture_retention_list = str(moisture_retention).split(',')
    available_water1_list = str(available_water1).split(',')
    hydraulic_conductivity_list = str(hydraulic_conductivity).split(',')

    # Use the length of the depth list to determine how many rows will be created
    max_length = max(len(depth_list), len(horizon_list), len(sand_list), len(slit_list), 
                     len(clay_list), len(bulk_density_list), len(particle_density_list), 
                     len(pore_space_list), len(moisture_retention_list), len(available_water1_list), 
                     len(hydraulic_conductivity_list))

    data_list = []

    for i in range(max_length):
        # Create a dictionary for each row with data from each list, using the same index for each column
        data = {
            'Pedon': pedon, 
            'Horizon': horizon_list[i % len(horizon_list)].strip(),  # Cycle through if not enough values
            'Depth (cm)': depth_list[i % len(depth_list)].strip(),
            'Loc X': loc_X, 
            'Loc Y': loc_Y,
            'Sand (%)': sand_list[i % len(sand_list)].strip(),
            'Slit (%)': slit_list[i % len(slit_list)].strip(),
            'Clay (%)': clay_list[i % len(clay_list)].strip(),
            'Bulk Density': bulk_density_list[i % len(bulk_density_list)].strip(),
            'Particle Density Mgm^-3': particle_density_list[i % len(particle_density_list)].strip(),
            'Pore Space (%)': pore_space_list[i % len(pore_space_list)].strip(),
            'Percent Moisture Retention (Mpa)': moisture_retention_list[i % len(moisture_retention_list)].strip(),
            'Available Water (%)': available_water1_list[i % len(available_water1_list)].strip(),
            'Hydraulic Conductivity (cm hr^-1)': hydraulic_conductivity_list[i % len(hydraulic_conductivity_list)].strip()
        }

        # Parse additional columns and their respective values
        if col_names and col_values:
            col_name_list = col_names.split(',')
            
            # Extract values in the format (value1,value2) using regex
            col_value_pattern = r"\(([^)]*)\)"
            col_value_list = re.findall(col_value_pattern, col_values)
            
            if len(col_name_list) == len(col_value_list):
                for col_name, col_value in zip(col_name_list, col_value_list):
                    col_value_split = col_value.split(',')
                    data[col_name.strip()] = col_value_split[i % len(col_value_split)].strip()
            else:
                st.error("The number of additional column names and values do not match!")
                st.stop()  # Prevent saving if there is an error

        data_list.append(data)

    # Save each row to Excel
    for data in data_list:
        append_to_excel(data)

    st.success("Data saved successfully!")
