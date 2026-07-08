import streamlit as st
import threading
import json

# Project is divided into separate files to manage different pages.
# This file stores the code that is used by multiple pages.

class GetAllSensorsThread(threading.Thread) :
	def __init__ (self, building_alias : str, mqtt_client_reference) :
		# Note : st.session_state.mqtt_client is not accessible as we're not in the main thread.
		# Consequently, it must be passed as a reference.
		threading.Thread.__init__(self)
		self.mqtt_client_reference = mqtt_client_reference
		# Retrieve the MQTT prefix to communicate on correct MQTT topic
		selected_building_index = list(st.session_state.available_buildings.values()).index(building_alias)
		self.building_mqtt_prefix = list(st.session_state.available_buildings.keys())[selected_building_index]

	def run(self) :
		# Runs when .start() is called.
		topic = f"{self.building_mqtt_prefix}/request"
		message = json.dumps({"command": "GetAvailableSensors"})
		self.mqtt_client_reference.publish(topic, message)