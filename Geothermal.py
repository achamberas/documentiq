import streamlit as st
import pandas as pd
import numpy as np

import plotly.express as px
import streamlit_plotly_mapbox_events as plotly_mapbox_events

import time

from utils.styles import *
from utils.auth import auth
from utils.connectors import *
from utils.components import doc_load_ui, stream_data
from utils.calculations import *
from utils.agents import *

add_styles()
# auth()

st.markdown('# Geothermal Risk Assessment')


def get_data():
    sql = """
        SELECT pd.id, displayName, account, totalValue, landValue, buildingValue, lastSalePrice, lastSaleDate, parcelArea, parcelAreaUnits, zoningCode, landUseCode,
        PARSE_NUMERIC(`Living Area`) as living_area, hf.description as heat_fuel, ht.description as heat_type,
        centroid[0] as latitude, centroid[1] as longitude
        FROM `gristmill5.rag_test.property_data` pd
        inner join gristmill5.rag_test.building_area ba
        on pd.account = ba.id
        inner join gristmill5.rag_test.construction_detail hf
        on pd.account = hf.id
        and hf.element = 'Heat Fuel'
        inner join gristmill5.rag_test.construction_detail ht
        on pd.account = ht.id
        and ht.element = 'Heat Type'
        where ba.`Living Area` not in ('ed', 'shed', '0')
    """

    sql = "SELECT * FROM gristmill5.rag_test.stjohns_tbl"

    st.session_state.data = bq_conn(sql)
    st.session_state.data['size'] = 5

def draw_map():
    color_palette = ['#C31D39','#6da84d','#AFC97E','#E2E4F6']
    color_palette = ['#6da84d','#C31D39']

    # Create a Plotly Mapbox figure
    # https://plotly.com/python-api-reference/generated/plotly.express.scatter_map.html
    mapbox = px.scatter_mapbox(st.session_state.data, lat="latitude", lon="longitude", hover_name="displayName", color="heat_type", size="size", color_discrete_sequence=color_palette, zoom=15.5, width=600, height=400)
    mapbox.update_layout(mapbox_style="carto-positron")
    mapbox.update_layout(showlegend=False)
    mapbox.update_layout(margin={"r":0, "t":0, "l":0, "b":0})
    mapbox.update_layout(dragmode="lasso")

    return mapbox

def selected_properties(mapbox_events):
    points = [p['pointNumber'] for p in mapbox_events[1]]
    selected = st.session_state.data[['displayName', 'living_area', 'heat_type']].iloc[points]
    selected['ceiling height'] = 8
    selected['occupants'] = np.ceil(selected['living_area'] / 500)
    selected['exterior doors'] = np.ceil(selected['living_area'] / 500)
    selected['windows'] = np.ceil(selected['living_area'] / 100)
    selected['required BTU'] = selected['living_area'] * selected['ceiling height'] + selected['occupants']*100 + selected['exterior doors']*1000 + selected['windows']*1000
    selected['tons HVAC'] = np.ceil(selected['required BTU'] / 12000)
    selected['HVAC sizes'] = selected['tons HVAC'].apply(lambda x: hvac_sizes(x))
    selected['Heat Type'] = selected['heat_type'].apply(lambda x: '🔴  ' + x if x in ['Hot Air-no Duc', 'Hot Water'] else '🟢  ' + x)

    specs = pd.read_csv('data/heat_pump_specs.csv')
    return selected[['displayName', 'living_area', 'Heat Type', 'required BTU', 'HVAC sizes']]

# Streamed response emulator
def response_generator(r):
    responses = [
        "👋 Hey there!  I am an autonomous agent that will help you evaluate the risk of geothermal projects.  To get started, lasso a collection of properties in the map below.",
        "👍 Great job!  Here are the properties that you selected, along with the estimated BTU and HVACs required.  If you want to change any of the inputs, edit the table and BTUs will be recalculated.  If you don't have any changes, click the button.",
    ]

    for word in responses[r].split():
        yield word + " "
        time.sleep(0.02)



# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.response_count = 0
    st.session_state.map_events = ([],[])
    st.session_state.looks_good = None
    st.session_state.permitting_requirements = None
    st.session_state.tax_incentives = None
    st.session_state.location = 'Queens, NY'

    get_data()

    with st.chat_message("assistant"):
        response = st.write_stream(response_generator(st.session_state.response_count))
        map = draw_map()
        st.session_state.map_events = plotly_mapbox_events.plotly_mapbox_events(
            map,
            click_event=True,
            select_event=True
        )
    st.session_state.response_count = st.session_state.response_count + 1
    st.session_state.messages.append({"role": "assistant", "content": response, "map": map})

else:
    # Display chat messages from history on app rerun
    for message in st.session_state.messages:

        # print(message["content"].__class__.__name__)
        # print(message["content"])

        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if 'map' in message:
                st.session_state.map_events = plotly_mapbox_events.plotly_mapbox_events(
                    message["map"],
                    click_event=True,
                    select_event=True
                )
            if 'dataframe' in message:
                st.data_editor(message["dataframe"], width=1500, hide_index=True)
            if 'buttons' in message:
               # print(st.session_state.looks_good)
               buttons = len(message["buttons"])
               button_tuple = tuple(None for _ in range(buttons))
               button_tuple = st.columns(buttons)
               for b in range(0, buttons):
                   with button_tuple[b]:
                       st.button(message["buttons"][b]["label"], key=message["buttons"][b]["key"])


if len(st.session_state.map_events[1]) > 0 and st.session_state.response_count == 1:
    selected = selected_properties(st.session_state.map_events)
    with st.chat_message("assistant"):
        response = st.write_stream(response_generator(st.session_state.response_count))
        st.data_editor(selected, width=1500, hide_index=True, key="orig")
        st.button("Looks good!", key="looks_good")

    st.session_state.response_count = st.session_state.response_count + 1
    st.session_state.messages.append({"role": "assistant", "content": response, "dataframe": selected, "buttons": [{"key":"looks_good", "label":"Looks good!"}]})

# Accept user input
if st.session_state.looks_good and st.session_state.response_count == 2:
    # Display assistant response in chat message container
    selected = selected_properties(st.session_state.map_events)

    non_duct, total_properties, total_living_area = statistics(selected)

    hvac_list = selected['HVAC sizes']
    hvacs = []
    for i in hvac_list:
        hvacs = hvacs + i

    fh = 0.75
    borehole_length = borehole_length(hvacs, fh)

    text_la = f"Your selections represent {total_properties} properties which include **{total_living_area} square feet** of living space.  "
    text_nd = '' if non_duct < 1 else f"However, ___{non_duct} of the properties do not have duct work___, which make them incompatible for heat pumps.  Duct work will need to be installed, increasing the total project cost.\n\n"
    text_bh = f"The length of the boreholes needed is **{borehole_length} feet.**"
    text = text_la + text_nd + text_bh

    with st.chat_message("assistant"):

        response = st.write_stream(stream_data(text))

        st.markdown(f"What do you want to learn about next?")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.button("Permitting Requirements", key="permitting_requirements")
        with col2:
            st.button("Tax Incentives", key="tax_incentives")
        with col3:
            st.button("Operational Plans", key="operational_plans")

    # Add assistant response to chat history
    st.session_state.messages.append({
        "role": "assistant", 
        "content": response, 
        "buttons": [
            {"key":"permitting_requirements", "label":"Permitting Requirements"},
            {"key":"tax_incentives", "label":"Tax Incentives"},
            {"key":"operational_plans", "label":"Operational Plans"}
        ]})

if st.session_state.permitting_requirements:
    with st.chat_message("assistant"):
        permitting = geothermal_permits(st.session_state.location)
        response = st.write_stream(stream_data(permitting))

    st.session_state.messages.append({"role": "assistant", "content": response})

if st.session_state.tax_incentives:
    with st.chat_message("assistant"):
        incentives = geothermal_incentives(st.session_state.location)
        response = st.write_stream(stream_data(incentives))

    st.session_state.messages.append({"role": "assistant", "content": response})

# Accept user input
if prompt := st.chat_input("What is up?"):

    st.session_state.messages.append({"role": "user", "content": prompt})

    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)
        # Add user message to chat history

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        response = st.write_stream(response_generator(st.session_state.response_count))

    st.session_state.response_count = st.session_state.response_count + 1
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})

