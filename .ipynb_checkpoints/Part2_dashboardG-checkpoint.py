import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt
from datetime import datetime as dt
from streamlit_keplergl import keplergl_static
from keplergl import KeplerGl
from datetime import datetime as dt
from PIL import Image
from numerize import numerize
import json
import os

############################################ INITIAL SETTINGS FOR THE DASHBOARD ##################################################

st.set_page_config(
    page_title="CitiBike Strategy Dashboard",
    page_icon="🚲",
    layout="wide"
)

# --- Title and Description ---
st.title("Citi Bikes Strategy Dashboard") 

### DEFINE SIDE BAR
st.sidebar.title('Aspect Selector') 
page = st.sidebar.selectbox('Select an aspect of the analysis',
                            ['Intro page',
                             'Weather component and bike usage',
                             'Most popular stations',
                             'Bike-type usage aligned to the Temperature',
                             'Interactive map with aggregated bike trips',
                             'Recommendations'])

################################################# IMPORT DATA #####################################################################

file_path = '/Users/runi/Final_Dashboard01.05/processed_data.csv'
            #/Users/runi/Downloads/2reduced_data_to_plot_7.csv
            #/Users/runi/Downloads/processed_data.csv
            #/Users/runi/citibike-analysis/2reduced_data_to_plot_7.csv
            #/Users/runi/citibike-analysis/6reduced_data_to_plot_7.csv

@st.cache_data
def load_data(path):
    try:
        df = pd.read_csv(path, index_col=0)
        df['date'] = pd.to_datetime(df['date'], format='%Y-%m-%d')
        for col in ['start_lat', 'start_lng', 'end_lat', 'end_lng']:
             if col in df.columns:
                 df[col] = pd.to_numeric(df[col], errors='coerce')
        # df.dropna(subset=['start_lat', 'start_lng'], inplace=True)
        return df
    except FileNotFoundError:
        st.error(f"Error: Data file not found at {path}.")
        return None
    except Exception as e:
        st.error(f"An error occurred while loading the data: {e}")
        return None

df = load_data(file_path) #


        #if df is not None:
            #st.write("Columns in the loaded DataFrame:")
            #st.write(df.columns)


top20 = pd.DataFrame() 
if df is not None:
    df_groupby_bar = df.groupby('start_station_name').size().reset_index(name='trip_count')
    top20 = df_groupby_bar.nlargest(20, 'trip_count')


############################################ DEFINE THE PAGES #####################################################################

### INTRO PAGE

if page == 'Intro page':
    st.markdown("#### This dashboard aims at providing helpful insights on the expansion problems Citi Bikes currently faces.") 
    st.markdown("Right now, Citi bikes runs into a situation where customers complain about bikes not being available at certain times. This analysis will look at the potential reasons behind this.")
    st.markdown("The dashboard is separated into 4 sections:") 
    st.markdown("- Weather component and bike usage")
    st.markdown("- Most popular stations") 
    st.markdown("- Interactive map with aggregated bike trips")
    st.markdown("- Recommendations")
    st.markdown("The dropdown menu on the left 'Aspect Selector' will take you to the different aspects of the analysis our team looked at.")

    try:
        myImage = Image.open("citi_bike_nyc_AP18117005853119.jpeg")
        st.image(myImage, caption="Source: https://ny1.com/nyc/all-boroughs/news/2024/09/14/bill-proposed-to-cap-citi-bike-at-cost-of-subway-ride") 
    except FileNotFoundError:
        st.error("Image not found")

######### LINE CHART PAGE: WEATHER COMPONENT AND BIKE USAGE

elif page == "Weather component and bike usage":

    st.header("Daily Bike Trips and Temperatures") 

    if df is not None and 'avgTemp' in df.columns:
        # --- Line Chart Data Wrangling ---
        # Calculate daily trip counts
        daily_rides = df.groupby('date').size().reset_index(name='trip_count')
        daily_temp = df[['date', 'avgTemp']].drop_duplicates().sort_values('date').reset_index(drop=True)
        df_line = pd.merge(daily_rides, daily_temp, on='date', how='left')

        # --- Create Dual-Axis Line Chart ---
        if not df_line.empty:
            fig_line = make_subplots(specs=[[{"secondary_y": True}]])
            fig_line.add_trace(go.Scatter(x=df_line['date'], y=df_line['trip_count'], name='Daily bike rides', marker={'color': 'blue'}), secondary_y=False,) 
            fig_line.add_trace(go.Scatter(x=df_line['date'], y=df_line['avgTemp'], name='Daily temperature', marker={'color': 'red'}), secondary_y=True,) 
            fig_line.update_layout(
                title='Daily bike trips and temperatures in 2022', 
                height=400 
            )
            fig_line.update_xaxes(title_text='Date') # Added x-axis title
            fig_line.update_yaxes(title_text='Number of Bike Rides', secondary_y=False) # Modified y-axis title
            fig_line.update_yaxes(title_text='Average Temperature', secondary_y=True) # Modified y-axis title
            st.plotly_chart(fig_line, use_container_width=True)
        else:
            st.warning("No data available for the daily rides vs temperature line chart.")
    elif df is None:
         st.warning("Data not loaded. Cannot display line chart.")
    else:
        st.warning("Average temperature data ('avgTemp' column) not found in the dataset. Cannot display line chart.")


    st.markdown("### Key Observations from the Chart:") 
    st.markdown("""
    1. **Strong Correlation**: There is a very clear positive correlation between the daily temperature and the number of daily bike rides throughout the year. As the red line (temperature) rises, the blue line (bike rides) tends to rise as well, and vice versa.
    2. **Seasonal Demand**: Both temperature and bike rides show distinct seasonal patterns, peaking during the warmer months (roughly April through October) and dropping significantly during the colder months (November through March).
    3. **Redistribution Gaps**: The highest volume of bike trips occurs during the summer months (July and August) when temperatures are consistently at their highest.
    4. **Temperature Swings Impact**: Short-term fluctuations in temperature appear to correspond with similar fluctuations in daily bike ride numbers, further emphasizing the immediate impact of weather on usage.
    """) 


### BAR CHART PAGE: MOST POPULAR STATIONS

elif page == 'Most popular stations':

    st.header("Most Popular Start Stations") 

    if df is not None and not top20.empty:
        # --- Display Total Rides Metric ---
        # Calculate total rides from the top 20 data
        total_rides = float(top20['trip_count'].sum())
        st.metric(label='Total Bike Rides', value=numerize.numerize(total_rides))

        # --- Create Bar Chart ---
        fig_bar = go.Figure(
            go.Bar(
                x=top20['trip_count'],
                y=top20['start_station_name'],
                orientation='h', # Set orientation to horizontal
                marker={'color': top20['trip_count'], 'colorscale': 'Blues'}
            )
        )
        fig_bar.update_layout(
            title='Top 20 most popular bike stations',
            xaxis_title='Sum of trips', 
            yaxis_title='Start stations', 
            width=900, 
            height=600 
        )
        st.plotly_chart(fig_bar, use_container_width=True)
    elif df is None:
         st.warning("Data not loaded. Cannot display bar chart.")
    else:
        st.warning("No data available for the top stations bar chart.")

    st.markdown("### Key Observations from the Chart:")
    st.markdown("""
    1. **Dominant Stations**: "Grove St PATH" stands out significantly as the most popular station by a considerable margin, followed by "South Waterfront Walkway - Sinatra Dr & 1 St", "Hoboken Terminal - River St & Hudson Pl", and "Hoboken Terminal - Hudson St & Hudson Pl". These few stations account for a very high number of trips, indicating they are major hubs.
    2. **Steep Drop-off**: There is a noticeable drop in trip volume after the top few stations. While the top 20 are shown, the difference between the trips from the most popular and the 20th most popular is substantial, highlighting a skewed distribution of usage among even the top stations.
    3. **Geographic Concentration**: Many of the top stations (e.g., Hoboken Terminal stations, Grove St PATH, South Waterfront Walkway) appear to be concentrated in key areas, likely near transport hubs or popular destinations in Jersey City/Hoboken.
    4. **Varied Activity within Top 20:**: Even within the top 20, there's a clear tiering, with the top few stations having well over 30,000 trips, while those lower down are in the 14,000-15,000 trip range.
    """) 
    st.markdown("### Insights:") 
    st.markdown("""
    - Stations with exceptionally high trip volumes, like "Grove St PATH", are critical points for potential bike shortages and require robust strategies for supply and redistribution, especially during peak times.
    - The skewed usage suggests that focusing efforts on ensuring adequate supply at the top handful of stations could address a significant portion of potential availability issues.
    - The concentration of popular stations might indicate key areas where demand consistently outstrips supply or where infrastructure could be expanded.
    - Understanding the specific times of day and days of the week when the most popular stations experience peak demand is crucial for optimizing bike redistribution.
    """)


elif page == 'Bike-type usage aligned to the Temperature':

    st.header("Classic vs Electric Bike Rentals by Temperature") # Added header for the page

    if df is not None and 'rideable_type' in df.columns and 'avgTemp' in df.columns:
        # Filter DataFrame by category
        classic_bike = df[df['rideable_type'] == 'classic_bike']
        electric_bike = df[df['rideable_type'] == 'electric_bike']

        # Create histograms for each category
        hist_data_A = go.Histogram(x = classic_bike['avgTemp'], name = 'Classic Bike', marker = dict(color = 'blue'))
        hist_data_B = go.Histogram(x = electric_bike['avgTemp'], name = 'Electric Bike', marker = dict(color = 'lightblue'))

        # Create layout
        layout = go.Layout(
            title = 'Classic vs Electric Bike Rentals by Temperature',
            xaxis = dict(title = 'Average Temperature'),
            yaxis = dict(title = 'Frequency'),
            barmode = 'overlay' # Overlay the histograms
        )

        # Create the figure
        fig3 = go.Figure(data = [hist_data_A, hist_data_B], layout = layout)

        # Display the figure
        st.plotly_chart(fig3)

        st.markdown('### Analysis of Classic vs Electric Bike Usage:') # Added markdown header
        st.markdown('This plot reveals distinct rental patterns between classic and electric bikes in relation to average temperature. We observe that the frequency of classic bike rentals is highly seasonal, mirroring temperature fluctuations, with a significant surge during warmer periods. This strong dependency means that as temperatures rise, the demand for classic bikes increases substantially. In contrast, electric bike rentals show a less pronounced relationship with temperature, maintaining a somewhat more consistent level of demand across different temperatures, although the overall volume is considerably lower than classic bikes.')
        st.markdown('The disparity in rental volume (classic bikes being rented much more frequently) combined with the electric bikes less seasonal usage suggests a few things for the business:')
        st.markdown('- The seasonal bike shortages reported by customers are likely driven primarily by the high, temperature-dependent demand for classic bikes during warmer months.')
        st.markdown('- While lower in volume, the demand for electric bikes exists even outside peak classic bike season. This indicates a segment of users who may prefer or rely on electric bikes regardless of weather, or perhaps turn to them when classic bikes are unavailable.')
        st.markdown('- The lower overall usage of electric bikes could be due to limited fleet size or availability at stations. If more electric bikes were available, their usage might increase, potentially absorbing some demand, especially during times or in locations where classic bikes are scarce.')
        st.markdown("Understanding these distinct usage patterns is crucial for Citi Bike's supply strategy. It highlights that addressing shortages requires not only managing the peak seasonal demand for classic bikes but also considering the role and availability of electric bikes in meeting overall user needs across different temperatures and times of the year.")
    elif df is None:
        st.warning("Data not loaded. Cannot display Classic vs Electric bikes histogram.")
    else:
        st.warning("Required columns ('rideable_type' or 'avgTemp') not found in the dataset to display Classic vs Electric bikes histogram.")




### MAP PAGE: INTERACTIVE MAP WITH AGGREGATED BIKE TRIPS

elif page == 'Interactive map with aggregated bike trips':

    st.header("Aggregated Bike Trips in New York") 
    st.write("Interactive map showing aggregated bike trips over New York")

    # --- Kepler.gl Map using HTML file ---
    map_file_path = "/Users/runi/Final_Dashboard01.05/nyc_bike_trips_map.html"

    try:
        with open(map_file_path, 'r', encoding='utf-8') as f:
            html_data = f.read()
        st.components.v1.html(html_data, height=500) 
    except Exception as e:
        st.error(f"An error occurred displaying the Kepler map: {e}")

    st.markdown("#### Using the filter on the left-hand side of the map we can check whether the most popular start stations also appear in the most popular trips.")
    st.markdown("### Key Observations:")
    st.markdown("""
1. **Busiest Manhattan Routes**: The densest trip routes are concentrated in Manhattan, particularly in Midtown, Flatiron, and the Financial District.
2. **Transport Hub Activity**: Intense bike traffic is observed near major transportation hubs like Grand Central, Penn Station, and ferry terminals.
3. **Recreational Popularity**: Areas such as Central Park and the Brooklyn waterfront (including Williamsburg and Dumbo) feature prominently in high-volume routes, indicating their popularity for recreational trips.
4. **High-Volume Areas**: These dense areas reflect significant commuter, tourist, and recreational cycling activity. """) 


### RECOMMENDATIONS PAGE

else: 
    st.header("Recommendations")
    try:
        
        bikes = Image.open("14820.jpg")
        st.image(bikes, caption="Photo from Freepik") 
    except FileNotFoundError:
        st.error("Image not found") 
    st.markdown("### Our analysis highlights key factors contributing to bike shortages and uneven usage patterns across Citi Bike stations, and provides recommendations for addressing these:")
    st.markdown("""
1.  **Seasonal Demand Fluctuations:** Bike usage is heavily influenced by temperature, with significant peaks during warmer months (April–October). This strong seasonal demand for classic bikes is a primary driver of reported shortages during this period.
2.  **Concentrated High Usage:** A small number of stations, particularly in key urban areas and near transport hubs, account for a disproportionately high volume of trips. This intense activity at specific locations creates significant local supply-demand imbalances.
3.  **Uneven Geographic Distribution of Demand:** While certain areas experience very high trip densities, other regions show lower activity. This unevenness impacts the efficient distribution and utilization of the bike fleet across the service area.
4.  **Distinct Bike Type Usage:** Classic bikes are the dominant mode of transport and their usage closely follows temperature. Electric bikes have lower overall usage and their demand is less seasonal, potentially serving different trip needs or being limited by availability.
5.  **Gaps in Fleet Management:** Existing bike redistribution strategies may not adequately cope with the scale and location-specific nature of peak demand and the differing usage patterns of classic versus electric bikes, leading to availability issues.
""")
    st.markdown("### Recommendations:")
    st.markdown("""
* **Implement Dynamic Seasonal Stocking:** Increase bike (especially classic bike) inventory at high-demand stations during warmer months (April-October) based on historical data and real-time demand predictions. Conversely, adjust stock levels in colder months to optimize resource allocation.
* **Enhance Redistribution at Key Hubs:** Develop more agile and frequent redistribution operations specifically targeting the top 20-30 most popular stations, particularly during peak commuter and recreational hours, to ensure bikes are available where demand is highest.
* **Optimize Fleet Mix and Availability:** Evaluate the current electric bike fleet size and distribution. Increasing the number and strategic placement of electric bikes could potentially absorb some classic bike demand, offer a more consistent option year-round, and cater to different user preferences or trip types.
* **Leverage Geospatial Insights for Redistribution:** Utilize detailed trip data and mapping tools (like Kepler.gl analysis) to identify specific high-traffic routes and origin-destination pairs, informing more targeted and efficient bike relocation efforts rather than just focusing on individual stations.
* **Explore Incentives for Redistribution:** Consider implementing user incentives (e.g., credits) for returning bikes to stations in areas experiencing shortages or for moving bikes from overstocked to understocked stations, complementing operational redistribution efforts.
""")














    
  