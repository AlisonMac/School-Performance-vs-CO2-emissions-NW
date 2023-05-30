import pandas as pd
import folium
import numpy as np
from pathlib import Path
from opencage.geocoder import OpenCageGeocode
from branca.colormap import LinearColormap

import os
print(os.listdir())
dataset_root = Path('d:/mapbubbles')
list(dataset_root.iterdir())
os.chdir(dataset_root)


key = ''  # opencagedata.com
geocoder = OpenCageGeocode(key)


df1 = pd.read_csv('2005-19_Local_Authority_CO2_emissions.csv')
df2 = pd.read_csv('2018-2019_england_ks2final.csv')

region = df1[(df1['Region'] == 'North West')]
year2019 = region[(region['Calendar Year'] == 2019)]

# Calculate average school performance for each town 
df2['TKS1AVERAGE'] = pd.to_numeric(df2['TKS1AVERAGE'], errors='coerce')
town_averages = df2.groupby('TOWN')['TKS1AVERAGE'].mean().reset_index()

# Merge CO2 emissions and school performance data
merged_data = year2019.merge(town_averages, left_on='Second Tier Authority', right_on='TOWN')

# Remove Cumbria from the data
merged_data = merged_data[merged_data['Second Tier Authority'] != 'Cumbria']

def get_color(value, min_value, max_value, low_color, high_color):
    value_normalized = (value - min_value) / (max_value - min_value)
    return np.array(low_color) + value_normalized * (np.array(high_color) - np.array(low_color))

min_performance = merged_data['TKS1AVERAGE'].min()
max_performance = merged_data['TKS1AVERAGE'].max()
min_emissions = merged_data['Territorial emissions (kt CO2)'].min()
max_emissions = merged_data['Territorial emissions (kt CO2)'].max()

m = folium.Map(location=[53.58333, -2.43333], tiles="OpenStreetMap", zoom_start=11)

performance_colormap = LinearColormap(['red', 'green'], vmin=min_performance, vmax=max_performance)
performance_colormap.caption = 'Average School Performance'
m.add_child(performance_colormap)

emissions_colormap = LinearColormap(['white', 'black'], vmin=min_emissions, vmax=max_emissions)
emissions_colormap.caption = 'CO2 Emissions (kt CO2)'
m.add_child(emissions_colormap)

for _, row in merged_data.iterrows():
    Town = row['Second Tier Authority']
    Area = row['Area (km2)']
    query = str(Town) + ',' + "England"

    results = geocoder.geocode(query)
    lat = results[0]['geometry']['lat']
    lng = results[0]['geometry']['lng']

    performance_color = get_color(row['TKS1AVERAGE'], min_performance, max_performance, [255, 0, 0], [0, 255, 0])
    performance_color = '#%02x%02x%02x' % tuple(performance_color.astype(int))

    emissions_color = get_color(row['Territorial emissions (kt CO2)'], min_emissions, max_emissions, [255, 255, 255], [0, 0, 0])
    emissions_color = '#%02x%02x%02x' % tuple(emissions_color.astype(int))

    folium.Circle(
        location=[lat, lng],
        popup=Town,
        radius=(Area * 10),
        color=emissions_color,
        weight=5,  # Thicker border
        fill=True,
        fill_color=performance_color,
        fill_opacity=0.8
    ).add_to(m)

m.save('north_west_bubbles.html')