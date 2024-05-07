import streamlit as st  # For creating the web app
import folium # For creating maps
from streamlit_folium import folium_static 
import pandas as pd # For data manipulation
import matplotlib.pyplot as plt

from sodapy import Socrata
import geopandas as gpd
from shapely.geometry import Point
from datetime import datetime, timedelta


datasource_url='data.cityofnewyork.us'
data_set_key='43nn-pn8j'
app_token='U0ejMExTXOGFff65poQxqcwZn'

client= Socrata(datasource_url,app_token)

client_timeout=240

results1= client.get(data_set_key,limit=50000)
results2= client.get(data_set_key,limit=50000,offset=50000)
results3= client.get(data_set_key,limit=50000,offset=100000)
results4= client.get(data_set_key,limit=50000,offset=150000)
results5= client.get(data_set_key,offset=200000)

df1=pd.DataFrame.from_records(results1)
df2=pd.DataFrame.from_records(results2)
df3=pd.DataFrame.from_records(results3)
df4=pd.DataFrame.from_records(results4)
df5=pd.DataFrame.from_records(results5)


all_dfs = [df1, df2, df3, df4,df5]
df = pd.concat(all_dfs, ignore_index=True)
df = df.dropna(subset=['dba','latitude', 'longitude'])
df.drop(['community_board', 'council_district', 'census_tract','bin', 'bbl', 'nta','violation_code'],inplace=True,axis=1)
df['address'] = df['building'] + ' ' + df['street'] + ', ' + df['boro'] + ', ' + df['zipcode'].astype(str) 
df.drop(['building', 'street'],inplace=True,axis=1)
df["latitude"] = pd.to_numeric(df["latitude"], errors='coerce')
df["longitude"] = pd.to_numeric(df["longitude"], errors='coerce')
df['camis'] = df['camis'].fillna(0).astype(int)
df['zipcode'] = df['zipcode'].fillna(0).astype(int)
df['score'] = df['score'].fillna(0).astype(int)  # Fill missing scores with 0 before converting to integer
df['inspection_date'] = pd.to_datetime(df['inspection_date'])
df['grade_date'] = pd.to_datetime(df['grade_date'])
df['record_date'] = pd.to_datetime(df['record_date'])
df['grade'] = df['grade'].astype(str)
grades_to_consider = ['A', 'B', 'C']
df= df[df['grade'].isin(grades_to_consider)]

#df = pd.read_csv("inspection.csv")# Setup the sidebar for user input
st.header("Know Your Favourite Restaurant")
st.sidebar.header('Search Options')
# Input box for restaurant name
restaurant_name = st.sidebar.text_input('Restaurant Name')
# Dropdown for grade selection
grade = st.sidebar.selectbox('Grade', ['-- Select Grade --', 'A', 'B', 'C'])
# Dropdown for food type selection, dynamically populated with unique values from the data
food_type = st.sidebar.selectbox('Food Type', ['-- Select Food Type --'] + list(df['cuisine_description'].unique()))
# Dropdown for borough selection, dynamically populated with unique values from the data
borough = st.sidebar.selectbox('Borough', ['-- Select Borough --'] + list(df['boro'].unique()))
# Button to trigger the search
search_button = st.sidebar.button('Search')
selected_restaurant = ""
selected_restaurant_locations=''

# Define a function to create a map based on filtered data
def create_map(data):
    # Set initial map location to New York City
    start_coords = (40.7128, -74.0060)
    folium_map = folium.Map(location=start_coords, zoom_start=12)
    # Iterate over the DataFrame and add markers for each restaurant
    for index, row in data.iterrows():
        folium.Marker(
            [row['latitude'], row['longitude']],
            tooltip=f"{row['dba']} (Grade: {row['grade']}, Cuisine: {row['cuisine_description']})" # Show the restaurant name when hovering over the marker
        ).add_to(folium_map)
    folium_static( folium_map)
def plot_critical_flag(selected_restaurant,selected_restaurant_locations):
    df_filtered=filtered_data[(filtered_data['dba'] == selected_restaurant) & (filtered_data['address'] == selected_restaurant_locations)]
    plt.figure(figsize=(10, 6))
    plt.plot(df_filtered['inspection_date'], df_filtered['critical_flag'], marker='o')
    plt.title(f'Critical Flag Variation for {selected_restaurant}')
    plt.xlabel('Inspection Date')
    plt.ylabel('Critical Flag')
    plt.xticks(rotation=45)
    plt.tight_layout()
    st.pyplot(plt)

def display_details(selected_restaurant,selected_restaurant_locations):
    restaurant_details = filtered_data[(filtered_data['dba'] == selected_restaurant) & (filtered_data['address'] == selected_restaurant_locations)]
    # Displaying restaurant details
    st.write('### Restaurant Details')
    st.write(f"**Name:** {restaurant_details['dba'].unique()}")
    st.write(f"**Grade:** {restaurant_details['grade'].unique()}")
    st.write(f"**Cuisine Type:** {restaurant_details['cuisine_description'].unique()}")
    st.write(f"**Borough:** {restaurant_details['boro'].unique()}")
    # Displaying violations spotted
    st.header(f"Here are violations spotted in {selected_restaurant} at {selected_restaurant_locations}")
    st.table(restaurant_details[['inspection_date', 'violation_description', 'critical_flag']])
    # Calculating and displaying average score
    average_score = restaurant_details['score'].mean()
    st.write(f"Overall score of {selected_restaurant} is {average_score}")
    # Function to categorize grade
    def categorize_grade(score):
        if score >= 27:
            return 'C'
        elif score >= 14:
            return 'B'
        else:
            return 'A'
    
    # Calculating overall grade
    overall_grade = categorize_grade(average_score)
    st.write(f"Overall grade of {selected_restaurant} is {overall_grade}")

# Filter the DataFrame based on the user's inputs. 
filtered_data = df[(df['dba'].str.contains(restaurant_name)) & 
                       (df['grade'] == grade) & 
                       (df['cuisine_description'] == food_type) & 
                       (df['boro'] == borough)]
# Display the results if any restaurants match the criteria
if not filtered_data.empty:
    st.write(f"Found some restaurants matching the criteria.")
    # Create and display the map with filtered results
    map_object = create_map(filtered_data)
    st.write('### Detailed View')
    st.dataframe(filtered_data)
    # Dropdown for selecting a restaurant
    selected_restaurant = st.selectbox('Select a Restaurant to View Details:', options=filtered_data['dba'].unique())
    
    selected_restaurant_locations=st.selectbox('select location of the restaurant:',options=filtered_data[filtered_data['dba'] == selected_restaurant]['address'].unique())

else:
    st.write("No matching restaurants found. Try adjusting the search filters.")
display_details(selected_restaurant,selected_restaurant_locations)
create_map(filtered_data[(filtered_data['dba'] == selected_restaurant) & (filtered_data['address'] == selected_restaurant_locations)])
plot_critical_flag(selected_restaurant,selected_restaurant_locations)


