import streamlit as st
import requests
'''
# Prevision des tarifs de Course de Taxi - Taxifare Predict
'''

st.markdown('''
Simulation de la vie d'un model en production. Made with ❤️ pour le 🚃
''')
datetime = st.text_input('Date & Time', '2014-07-06 19:18:00')
pickup_longitude = st.text_input('Pickup Longitude', '-73.950655')
pickup_latitude = st.text_input('Pickup Latitude', '40.783282')
dropoff_longitude = st.text_input('Drop Off Longitude', '-73.984365')
dropoff_latitude = st.text_input('Drop Off Latitude', '40.769802')
passenger_count = st.slider('Choose the number of passenger', 1, 10, 3)

url = f"https://taxifare-161041691439.europe-west1.run.app/predict?pickup_datetime={datetime}&pickup_longitude={pickup_longitude}&pickup_latitude={pickup_latitude}&dropoff_longitude={dropoff_longitude}&dropoff_latitude={dropoff_latitude}&passenger_count={passenger_count}"

data = "test"

def callpi() :
    data = requests.get(url).json()
    return data

if st.button("Predict"):
    data = callpi()
    st.text(f"Prédiction du prix de la course : {data['fare']} $")
