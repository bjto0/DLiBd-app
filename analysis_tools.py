import streamlit as st
import time
import datetime
from shared_code import *
from urllib.request import urlretrieve
import pandas as pd
import numpy as np
import math
import plotly.express as px

if "checkbox_count" not in st.session_state :
	st.session_state.checkbox_count = 0
if "submit_button_clicked" not in st.session_state :
	# Necessary to determine wether or not rerun was made because of a change outside the form
	# or because the user clicked the submit button
	st.session_state.submit_button_clicked = False
if "current_tool" not in st.session_state :
	# Used to detect when to reset st.session_state.submit_button_clicked
	st.session_state.current_tool = ""
	
def on_submit() :
	st.session_state.submit_button_clicked = True

def json_histories_to_df (full_json : list) :
	'''
	Converts JSON histories to pandas dataframe, so it can correctly be displayed by Streamlit
	'''
	general_df = []
	for sensor_data in full_json :
		sensor_name = sensor_data["sensor_name"]

		if len(sensor_data["records"]) > 0 :
			sensor_records = sensor_data["records"]

			# Contains two rows: datetime and value
			sensor_df = pd.DataFrame(sensor_records)
			# Convert strings to proper datetime.datetime objects
			sensor_df["datetime"] = pd.to_datetime(sensor_df["datetime"], format = "%d-%m-%Y %H:%M:%S")

			# Set datetime as index column (instead of auto-increment int)
			sensor_df = sensor_df.set_index("datetime")
			# Rename "value" column to sensor name
			sensor_df = sensor_df.rename(columns = {"value": sensor_name})

			general_df.append(sensor_df)

		else :
			st.warning("Une ou plusieurs sondes ne contient aucune donnée pour la période sélectionnée.")

	# Finally, merge DataFrames horizontally (axis = 1) as they have a common datetime column.
	# This means all similar datetimes will be combined into a single row.
	general_df = pd.concat(general_df, axis = 1, sort = True)
	return general_df


st.markdown("## Outils d'analyse")

selected_type = st.selectbox("Type de données à analyser :", ["CO2", "Température"])

# CO2 and temperature don't exactly havec the same tools.
common_tools = ["Aucun", "Visualiser historique - tableau", "Visualiser historique - graphique", "Heures d'inconfort"]
if selected_type == "CO2" :
	selected_tool = st.selectbox("Choississez un outil à appliquer :", common_tools + ["Indice ICONE"])
else :
	selected_tool = st.selectbox("Choississez un outil à appliquer :", common_tools)


checkboxes_values = {}

if selected_tool != "Aucun" :

	# Reload available sensors if we changed tool.
	if selected_tool != st.session_state.current_tool :
		st.session_state.submit_button_clicked = False
	st.session_state.current_tool = selected_tool

	if len(st.session_state.available_buildings) != 0 :
		# If button was clicked, we don't want to run this part again.
		if not st.session_state.submit_button_clicked :
			# Request all sensors of all buildings. Empty existing values.
			st.session_state.received_all_sensors = {}
			getting_sensors_info = st.info("Récupération des capteurs…")
			get_all_sensors_threads = []
			for building_alias in st.session_state.available_buildings.values() :
				t = GetAllSensorsThread(building_alias, st.session_state.mqtt_client)
				get_all_sensors_threads.append(t)
				t.start()
			for t in get_all_sensors_threads :
				# Correctly stop threads. Not executed when values are retrieved. on_message callback will set value of dict in st.session_state
				t.join() 
			
			# Loop to check if we got all the desired data. Timeout 5 seconds.
			for second in range (0, 5) :
				time.sleep(1)
				if len(st.session_state.received_all_sensors) == len(st.session_state.available_buildings) :
					# We have received sensors of all building. Don't wait any extra second
					break
			getting_sensors_info.empty()
			if len(st.session_state.received_all_sensors) != len(st.session_state.available_buildings) :		
				st.warning("Attention : les données d'un ou plusieurs bâtiments sont manquantes.")		

		# Once we got all values or if we already had them, create a form to allow the user to select the sensors to consider.
		# The dictionnary is constructed as followed : {building1_prefix: [(sensorA_key, False), (sensorB_key, True)...], building2_prefix: [...] ...}
		# An iteration through it will allow to get the keys of the selected sensors for each building.
		checkboxes_values = {}
		with st.form("Paramètres de la sélection") :
			for building_mqtt_prefix, sensors in st.session_state.received_all_sensors.items() :
				checkboxes_values[building_mqtt_prefix] = []
				building_alias = st.session_state.available_buildings[building_mqtt_prefix]
				building_expander = st.expander(building_alias)
				for floor_data in sensors["floors"] :
					floor_expander = building_expander.expander(floor_data["floor_alias"])
					for sensor_data in floor_data["sensors"] :
						check_box = floor_expander.checkbox(sensor_data["sensor_alias"])
						# Add tuple (sensor_key, checkbox boolean)
						checkboxes_values[building_mqtt_prefix].append((sensor_data["sensor_key"], check_box))
						st.session_state.checkbox_count += 1
			
			# Date input
			min_value = datetime.date(2026, 1, 1)
			max_value = datetime.datetime.today()
			default_value = (max_value - datetime.timedelta(days = 7), max_value)
			(start_date, end_date) = st.date_input("Sélectionnez la période de données", default_value, min_value, max_value, format = "DD/MM/YYYY")
			
			if selected_tool == "Heures d'inconfort" :
				# For this tool, we need two extra parameters.
				discomfort_columns = st.columns(2)
				default_threshold = 1200 if selected_type == "CO2" else 28
				min_threshold = 700 if selected_type == "CO2" else 25
				max_threshold = 2000 if selected_type == "CO2" else 35
				discomfort_threshold = discomfort_columns[0].number_input("Seuil d'inconfort", min_threshold, max_threshold, default_threshold, 1)

				discomfort_step = discomfort_columns[1].number_input("Intervalle de temps moyen (15 min → 0.25 heure par enregistrement)",
														 1, 1440, 15, 1)


			submit_button = st.form_submit_button("Valider", on_click = on_submit)
			# We can't directly call actions here, under if submit_button: 
			# because clicking the button causes the whole script to rerun
			# and retrieving sensors is fired again. Instead, use a callback and a session state bool

			# Get selected sensor keys
			if st.session_state.submit_button_clicked :
				selected_sensors = {}
				for building_prefix, sensor_tuples in checkboxes_values.items() :
					selected_sensors[building_prefix] = []
					for (sensor_key, sensor_checked) in sensor_tuples :
						if sensor_checked :
							selected_sensors[building_prefix].append(sensor_key)

				is_at_least_one_sensor_selected = [len(s) > 0 for s in selected_sensors.values()]
				if True in is_at_least_one_sensor_selected :
					# Send history request to all devices for which at least 1 sensor was selected
					sent_histories_request = 0
					for building_prefix, sensors_keys in selected_sensors.items() :
						if len(sensors_keys) > 0 :
							# Don't send anything if no sensors were selected for that building
							message = json.dumps({"command": "GetHistories", "sensors_keys": sensors_keys, "is_co2": selected_type == "CO2",
								"start_date": start_date.strftime("%d-%m-%Y"), "end_date": end_date.strftime("%d-%m-%Y"),
								"building_alias": st.session_state.available_buildings[building_prefix]})
							st.session_state.mqtt_client.publish(f"{building_prefix}/request", message)
							sent_histories_request += 1

					getting_histories_info = st.info("Récupération des historiques...")
					 # Wait for response. Timeout at 5 seconds. App will receive a URL on topic /url
					st.session_state.url_to_load = []
					for second in range (0, 5) :
						time.sleep(1)
						if len(st.session_state.url_to_load) == sent_histories_request :
							break # Received all URL. Exit loop when we get it.
					getting_histories_info.empty()
					if len(st.session_state.url_to_load) == 0 :		
						st.error("Aucune donnée n'a pu être récupérée.")
					else :
						# If at least one sensor history has been retrieved, display it anyway
						if len(st.session_state.url_to_load) != sent_histories_request :
							st.warning("Attention: certains historiques n'ont pas pu être récupérés.")
						# Download all files individually and combine all lists into a single one
						full_json = []
						for i, url in enumerate(st.session_state.url_to_load) :
							path, headers = urlretrieve(url, f"temp_histories_{i}.json")
							with open(path, 'r') as json_file :
								full_json += json.load(json_file) # Concatenate lists

						full_df = json_histories_to_df(full_json)
			
						# At this point, we can finally switch on the selected tool
						if selected_tool == "Visualiser historique - tableau" :
							# Add mean column to df, ignoring NaN values
							full_df["Moyenne"] = full_df.mean(axis = 1, skipna = True)
							st.write(full_df)

						elif selected_tool == "Visualiser historique - graphique" :
							# Add mean column to df, ignoring NaN values
							full_df["Moyenne"] = full_df.mean(axis = 1, skipna = True)
							# st.line_chart is too elementary for us
							#full_df = full_df.replace(None, np.nan)
							fig = px.line(full_df, labels = {"datetime": "Date et heure", "value": "Valeur"})
							st.plotly_chart(fig, width = "stretch")
						
						elif selected_tool == "Heures d'inconfort" :
							if discomfort_threshold != None :
								discomfort_counts = (full_df > discomfort_threshold).sum() # Returns pd.Series of count by sensor
								discomfort_counts["Moyenne"] = discomfort_counts.mean()
								discomfort_hours = discomfort_counts * discomfort_step / 60
								# Convert Series to DataFrame and rename column for display
								st.write(discomfort_hours.to_frame("Heures d'inconfort sur la période sélectionnée"))

						elif selected_tool == "Indice ICONE" :
							st.markdown("Pour rappel :")
							st.latex(r'''ICONE = \Big( \frac{2.5}{\log_{10}(2)} \Big) \log_{10} (1 + f_1 + 3f_2)''')
							st.markdown(r'''Avec $f_1$ proportion de valeurs entre 1000 et 1700 ppm et $f_2$ proportion de valeurs supérieures à 1700 ppm. Seules les valeurs > 450 ppm sont prises en compte.''')
							# Replace > 1700 values by 2, < 1700 && > 1000 by 1, < 1000 && > 450 by 0, others by -1
							numpy_data = np.where(full_df > 1700, 2,
						  						np.where(full_df > 1000, 1, 
					   							np.where(full_df > 450, 0, -1)))
							# numpy_data is currently a numpy array so pandas can't keep the dataframe column names. Reinsert them manually.
							num_df = pd.DataFrame(numpy_data, columns = full_df.columns, index = full_df.index)
							# Calculate f1 and f2 for each sensor
							f1 = (num_df == 1).sum(axis = 0) / (num_df >= 0).sum(axis = 0)
							f2 = (num_df == 2).sum(axis = 0) / (num_df >= 0).sum(axis = 0)
							icone_value = (2.5/math.log10(2)) * np.log10(1 + f1 + 3*f2)
							icone_df = pd.DataFrame({"f1": f1, "f2": f2, "Indice ICONE": icone_value})
							st.write(icone_df)

						
				else :
					# User hasn't selected any sensor!
					st.error("Veuillez sélectionner au moins un capteur.")

else :
	# We selected no tool
	st.session_state.submit_button_clicked = False