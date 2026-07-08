import streamlit as st
import time
from shared_code import *

st.markdown("## Données en direct")

def init_values_display_frame () :
	'''
	Initializes default setup to display sensor values.
	'''
	building_floors = st.session_state.received_all_sensors[selected_building_mqtt_prefix]["floors"]
	floor_columns = st.columns(len(building_floors)) # Returns list
	for i, floor_data in enumerate(building_floors) :
		floor_columns[i].markdown(f"## {floor_data["floor_alias"]}") # Add floor alias as level two header
		for sensor_data in floor_data["sensors"] :
			sensor_expander = floor_columns[i].expander(f"{sensor_data["sensor_alias"]}")
			# Create 2 columns for CO2 and temperature
			sensor_data_columns = sensor_expander.columns(2)
			associated_topic = f"{selected_building_mqtt_prefix}/{floor_data["floor_id"]}/{sensor_data["sensor_key"]}"
			
			co2_placeholder = sensor_data_columns[0].empty()
			# Keep value to override st.empty markdown and set last known value to None
			st.session_state.topics_to_placeholders_values[associated_topic + "/co2"] = [co2_placeholder, None]
			
			temperature_placeholder = sensor_data_columns[1].empty()
			st.session_state.topics_to_placeholders_values[associated_topic + "/temperature"] = [temperature_placeholder, None]



@st.fragment(run_every = 5)
def view_data_live () :
	'''
	Updates all available sensor values and stylizes text.
	Function executed in a streamlit fragment, i.e. independently from the rest of the code.
	Looping every 5 seconds.
	'''
	for topic, (placeholder, value) in st.session_state.topics_to_placeholders_values.items() :
		if topic.split("/")[-1] == "co2" :
			display_text = (str(value) + " ppm" if value != None else "?")
			try :
				colored_display_text = f":green[{display_text}]" if int(value) < 700 else (
					f":orange[{display_text}]" if int(value) < 1000 else f":red[{display_text}]"
				)
			except :
				# Value can't be converted to int. Don't color it then.
				colored_display_text = display_text
		elif topic.split("/")[-1] == "temperature" :
			display_text = (str(value) + " °C" if value != None else "?")
			try :
				colored_display_text = f":blue[{display_text}]" if float(value) < 17 else (
					f":green[{display_text}]" if float(value) < 21 else f":red[{display_text}]"
				)
			except :
				# Value can't be converted to float. Don't color it then.
				colored_display_text = display_text
		
		if colored_display_text != "" :
			placeholder.markdown(colored_display_text, text_alignment = "center")

building_aliases = st.session_state.available_buildings.values()
selected_building_alias = st.selectbox("Choisissez un bâtiment:", ["Aucun"] + list(building_aliases))
if selected_building_alias != "Aucun" :
	# Retrieve associated MQTT topic prefix
	selected_building_index = list(st.session_state.available_buildings.values()).index(selected_building_alias)
	# Always works because alias and prefix attributes are marked unique
	selected_building_mqtt_prefix = list(st.session_state.available_buildings.keys())[selected_building_index]

	# Retrieve sensors by publishing a request (done in a seperate thread)
	# Don't forget to empty any previously saved value
	st.session_state.received_all_sensors = {}
	getting_sensors_info = st.info("Récupération des capteurs…")
	get_all_sensors_threads = []
	t = GetAllSensorsThread(selected_building_alias, st.session_state.mqtt_client)
	t.start()
	# Correctly stop the thread. Not executed when values are retrieved. on_message callback will set value of dict in st.session_state
	t.join()

	# Loop to check if we got all the desired data. Timeout 5 seconds.
	for second in range (0, 5) :
		time.sleep(1)
		if selected_building_mqtt_prefix in st.session_state.received_all_sensors :
			# We have received sensors of the building. Don't wait any extra second
			break
	getting_sensors_info.empty()
	if selected_building_mqtt_prefix not in st.session_state.received_all_sensors :		
		st.error("Données de sondes indisponibles.")
	else :
		init_values_display_frame()
		# Looping function
		view_data_live()