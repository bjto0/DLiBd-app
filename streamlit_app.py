import streamlit as st
from streamlit.runtime.scriptrunner import add_script_run_ctx, get_script_run_ctx
from random import randint
from paho.mqtt import client as paho_client
from threading import current_thread
import sqlite3
import json

broker = "192.168.12.1"
port = 1883
username = "dri"
password = "RosnySB@@93110"

ctx = get_script_run_ctx()

st.html("""
        <style>
        	.stMainBlockContainer {
				max-width:64rem;
        }
        </style>
        """)

home_page = st.Page("home.py", title = "Accueil")
live_view_page = st.Page("live_view.py", title = "Données en direct")
sensors_locations_page = st.Page("sensors_locations.py", title = "Localisation des appareils")
analysis_tools_page = st.Page("analysis_tools.py", title = "Outils d'analyse")
documentation_page = st.Page("dlibdoc.py", title = "Documentation")

# st.session_state variables
if "mqtt_client" not in st.session_state :
	st.session_state.mqtt_client = None
if "mqtt_client_connected" not in st.session_state :
	st.session_state.mqtt_client_connected = False
if "available_buildings" not in st.session_state :
    # Binds MQTT topic prefixes to aliases
    st.session_state.available_buildings = {}
if "received_all_sensors" not in st.session_state :
	# Dictionnary where key is building MQTT prefix and value is a dictionnary too
	# containing all floors and all sensors (see JSON object on RPI side)
	st.session_state.received_all_sensors = {}
if "received_histories" not in st.session_state :
	# Dictionnary where key is building alias and value is a list of sensor records.
	# Sensor records are a dictionnary with sensor alias and a list of records (a datetime and a value)
	st.session_state.received_histories = {}
if "topics_to_placeholders_values" not in st.session_state :
	# Key: topic (str); Value: [placeholder (st.empty), last known value (float or int as str)]
	st.session_state.topics_to_placeholders_values = {}
if "url_to_load" not in st.session_state :
	# Used to download large files with HTTP. Works like a queue of url
	st.session_state.url_to_load = []

def init_mqtt_client () :
	'''
	Initializes MQTT client for client side. Returns it if successful.
	'''
	try:
		client_id = f'python-mqtt-{randint(0, 999999)}'
		client = paho_client.Client(paho_client.CallbackAPIVersion.VERSION2, client_id)
		client.username_pw_set(username, password)
		client.on_connect = on_connect
		client.on_message = on_message
		client.connect(broker, port)
		# Subscribe to all topics related to this building
		# We use Streamlit multi-level wildcard '#'
		client.subscribe("#")
		client.loop_start()
		
	except Exception as e:
		print(f"Exception raised: {e}")
		st.session_state.mqtt_client_connected = False
		st.error("Connexion au serveur impossible")
	return client

def on_connect(client, userdata, flags, rc, properties) :
	# IMPORTANT: Streamlit doesn't support multithreading. However, MQTT uses a separate network thread.
	# We access PRIVATE ATTRIBUTE ._thread, as Paho MQTT doesn't expose the attribute by default.
	# The following line ensures st._session_state is accessible. Sadly, other Streamlit functions may not work.
	add_script_run_ctx(current_thread(), ctx)
	if rc == 0 :
		st.session_state.mqtt_client_connected = True
	else :
		print(f"Failed to connect. Return code {rc}")
		st.error("Connexion au serveur impossible")
		st.session_state.mqtt_client_connected = False
	st.rerun()

def on_message(client, userdata, msg) :
	add_script_run_ctx(current_thread(), ctx)
	# Very useful line for debugging
	#print(f"{msg.payload.decode("utf-8")} on {msg.topic}")

	# If we received all available sensors for a building
	if msg.topic.split("/")[-1] == "all_sensors" :
		building_mqtt_prefix = msg.topic.split("/")[0]
		# Add sensors dictionnary to session state
		st.session_state.received_all_sensors[building_mqtt_prefix] = json.loads(msg.payload.decode("utf-8"))

	# If we received a new sensor value
	elif msg.topic in st.session_state.topics_to_placeholders_values.keys() :
		# Override last saved value. Message received as JSON object '{"value": X}'
		value = json.loads(msg.payload.decode("utf-8"))["value"]
		st.session_state.topics_to_placeholders_values[msg.topic][1] = value

	# If we received an URL to get sensors locations images or histories
	elif msg.topic.split("/")[-1] == "url" :
		st.session_state.url_to_load.append(json.loads(msg.payload.decode("utf-8"))["url"])


@st.cache_data
def load_available_buildings () :
    '''
    Reads available buildings from "available_buildings.db". Streamlit cached.
    Returns a dictionnary with keys being MQTT topic prefixes and values aliases
    '''
    return_dict = {}
    con = sqlite3.connect("available_buildings.db")
    cur = con.cursor()
    res = cur.execute("SELECT mqtt_prefix, alias FROM buildings;").fetchall()
    for row in res :
        return_dict[row[0]] = row[1]
    return return_dict


# Branch depending on whether connection to MQTT client is already established
if st.session_state.mqtt_client_connected == False :
	# Display only home page
	pg = st.navigation((home_page, documentation_page))
	pg.run()
	st.info("Connexion au serveur MQTT en cours…")
	st.session_state.mqtt_client = init_mqtt_client()
	# on_connect callback will rerun the script


else :
	# Display this success message as a header
	st.success("Connecté au serveur !")
	pg = st.navigation((home_page, live_view_page, sensors_locations_page, analysis_tools_page, documentation_page))
	pg.run()
	#print("Connected to MQTT broker")
	st.session_state.available_buildings = load_available_buildings()