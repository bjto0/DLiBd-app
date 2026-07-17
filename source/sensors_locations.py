import streamlit as st
import time
import json
from urllib.request import urlretrieve
import pydeck as pdk
import pandas as pd
import base64
import sqlite3

# AT CITY SCALE
st.markdown("## Localisation des bâtiments")

# It's not possible to directly use local data in pydeck, because
# CORS policy prohibits HTML pages from reading local files.
# The alternative is to transform file into a base64 str, integrated in the HTML page.
def transform_file_to_base64_str (path : str, mime_type : str) :
    '''
    Translates file to base64 string, so that it can be used in pydeck generated HTML pages.
    Input mime_type : associated HTML MIME type.
    '''
    with open(path, "rb") as f :
        encoded_string = base64.b64encode(f.read()).decode('utf-8')
        data_url = f"data:{mime_type};base64,{encoded_string}"
    return data_url

def load_buildings_geodata(marker_icon_data) :
    '''
    Reads available_buildings.db to extract geodata. Adds marker icon data to each element.
    Returns a list of dictionnaries.
    '''
    buildings_data = []
    con = sqlite3.connect("available_buildings.db")
    cur = con.cursor()
    res = cur.execute("SELECT alias, longitude, latitude FROM buildings;").fetchall()
    for row in res :
        buildings_data.append({"alias": row[0], "longitude": row[1], "latitude": row[2], "icon_data": marker_icon_data})
    return buildings_data

# Marker icon to use
icon_data = {
    "url": transform_file_to_base64_str("location_marker.png", "image/png"),
    "width": 192,
    "height": 129,
    "anchorY": 129
}

buildings_geodata = load_buildings_geodata(icon_data)

# Set initial view
view_state = pdk.ViewState(longitude = 2.485, latitude = 48.878, zoom = 14, pitch = 50)

# Parameters get_icon et get_position are related to the name of keys in the dictionnaries
icon_layer = pdk.Layer(type ="IconLayer", data = buildings_geodata, get_icon = "icon_data",
                       get_size = 4, pickable = True, size_scale = 15, get_position = "[longitude, latitude]")

# Tooltip for when we hover marker with mouse
tooltip = {
   "html": "<b>Bâtiment :</b> {alias}",
   "style": {
        "backgroundColor": "steelblue",
        "color": "white",
        "font": "sans-serif"
   }
}

# This may not work if not connected to Internet. Styles are provided by CARTO.
map_styles = {"dark": "Sombre", "light": "Clair", "road": "Voirie"}
mapstyle = st.selectbox("Style de carte :", options = list(map_styles.keys()), format_func = lambda x: map_styles[x], width = 200)
#mapstyle = "light"
final_map = pdk.Deck(map_style = f"{mapstyle}", layers = [icon_layer], initial_view_state = view_state, tooltip = tooltip)
st.pydeck_chart(final_map)
st.markdown("<div style = 'text-align: center'> Maintenir clic gauche pour déplacer, maintenir Shift + clic gauche pour tourner </div>",
			unsafe_allow_html = True)


# AT BUILDING SCALE
st.markdown("## Plans de localisation des sondes")

building_aliases = st.session_state.available_buildings.values()
selected_building_alias = st.selectbox("Choisissez un bâtiment:", ["Aucun"] + list(building_aliases))

if selected_building_alias != "Aucun" :
	# Retrieve associated MQTT topic prefix
	selected_building_index = list(st.session_state.available_buildings.values()).index(selected_building_alias)
	# Always works because alias and prefix attributes are marked unique
	st.session_state.selected_building_mqtt_prefix = list(st.session_state.available_buildings.keys())[selected_building_index]

	# Subscribe to all topics related to this building, except the /request topic
	# We use Streamlit multi-level wildcard '#'
	st.session_state.mqtt_client.unsubscribe("#")
	st.session_state.mqtt_client.subscribe(f"{st.session_state.selected_building_mqtt_prefix}/#")
	st.session_state.mqtt_client.unsubscribe(f"{st.session_state.selected_building_mqtt_prefix}/request")

	# Retrieve sensors by publishing a request
	getting_locations_info = st.info("Récupération de la nomenclature…")
	topic = f"{st.session_state.selected_building_mqtt_prefix}/request"
	message = json.dumps({"command": "GetSensorsLocations"})
	st.session_state.mqtt_client.publish(topic, message)
	
    # Wait for response. Timeout at 5 seconds. App will receive a URL on topic /url
	st.session_state.url_to_load = []
	for second in range (0, 5) :
		time.sleep(1)
		if len(st.session_state.url_to_load) != 0 :
			break # App is only waiting for 1 URL. Exit loop when we get it.
	getting_locations_info.empty()
	if len(st.session_state.url_to_load) == 0 :		
		st.error("Nomenclature indisponible.")
	else :
		# Download file and load image
		path, headers = urlretrieve(st.session_state.url_to_load[0], "temp_sensors_locations.png")
		st.image(path, caption = f"Localisation des capteurs pour le site \
		   {selected_building_alias}", width = "stretch")