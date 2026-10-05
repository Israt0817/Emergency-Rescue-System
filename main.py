import streamlit as st
from streamlit_folium import st_folium

from src.ui_components import (
    render_location_settings,
    render_interaction_controls,
    render_route_search_controls,
    render_routing_settings,
    render_metrics,
)
from src.location_service import get_browser_location, geocode_place_name
from src.map_utils import load_graph_network, generate_map_view
from src.algorithm import calculate_route
from src.route_utils import find_nearest_node_custom
from src.hazard import apply_hazard


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    layout="wide",
    page_title="AI Emergency Rescue System"
)


# ============================================================
# SESSION STATE
# ============================================================

if "location_coords" not in st.session_state:
    st.session_state.location_coords = None

if "location_name" not in st.session_state:
    st.session_state.location_name = "Detecting Your Location..."

if "gps_initialized" not in st.session_state:
    st.session_state.gps_initialized = False

if "manual_location" not in st.session_state:
    st.session_state.manual_location = False

if "hazard_history" not in st.session_state:
    st.session_state.hazard_history = []

if "last_processed_click" not in st.session_state:
    st.session_state.last_processed_click = None


# ============================================================
# GET USER'S LIVE BROWSER LOCATION
# ============================================================

browser_location = get_browser_location()

if (
    not st.session_state.manual_location
    and not st.session_state.gps_initialized
    and browser_location is not None
):
    try:
        user_lat = float(browser_location["coords"]["latitude"])
        user_lon = float(browser_location["coords"]["longitude"])

        st.session_state.location_coords = (user_lat, user_lon)
        st.session_state.location_name = "Your Current Location"
        st.session_state.gps_initialized = True

        st.session_state.pop("start_node", None)
        st.session_state.pop("goal_node", None)
        st.session_state.hazard_history = []
        st.session_state.last_processed_click = None

        st.cache_data.clear()
        st.rerun()

    except (KeyError, TypeError, ValueError):
        pass


# ============================================================
# SIDEBAR UI
# ============================================================

entered_location, submit_location, refresh_map = render_location_settings()


# ============================================================
# PROCESS MANUAL LOCATION
# ============================================================

if submit_location:
    if entered_location.strip():
        with st.spinner("Finding location..."):
            coords = geocode_place_name(entered_location.strip())

        if coords:
            st.session_state.manual_location = True
            st.session_state.location_name = entered_location.strip()
            st.session_state.location_coords = coords

            st.session_state.pop("start_node", None)
            st.session_state.pop("goal_node", None)
            st.session_state.hazard_history = []
            st.session_state.last_processed_click = None

            st.cache_data.clear()
            st.rerun()
        else:
            st.sidebar.error(
                "Location not found. Try a more specific location."
            )


# ============================================================
# REFRESH MAP
# ============================================================

if refresh_map:
    st.cache_data.clear()
    st.session_state.hazard_history = []
    st.session_state.last_processed_click = None
    st.rerun()


# ============================================================
# MAP INTERACTION + HAZARD CONTROLS
# ============================================================

selection_mode, hazard_tool, clear_hazards = render_interaction_controls()

if clear_hazards:
    st.session_state.hazard_history = []
    st.session_state.last_processed_click = None
    st.rerun()


# ============================================================
# START / DESTINATION SEARCH + ROUTING SETTINGS
# ============================================================

start_input, submit_start, dest_input, submit_dest = render_route_search_controls()
agent_mode, algorithm, theme_key = render_routing_settings()


# ============================================================
# WAIT FOR GPS
# ============================================================

if st.session_state.location_coords is None:
    st.info(
        "📍 Detecting your current location...\n\n"
        "Please allow location access in your browser."
    )
    st.stop()


# ============================================================
# CURRENT LOCATION + LOAD ROAD NETWORK
# ============================================================

latitude, longitude = st.session_state.location_coords

with st.spinner(
    f"Loading map network for {st.session_state.location_name}..."
):
    graph = load_graph_network(latitude, longitude)

nodes = list(graph.nodes())

if not nodes:
    st.error("Could not create a road network for this location.")
    st.stop()


# ============================================================
# DEFAULT START / DESTINATION
# ============================================================

if (
    "start_node" not in st.session_state
    or st.session_state.start_node not in graph
):
    st.session_state.start_node = find_nearest_node_custom(
        graph,
        latitude,
        longitude
    )

if (
    "goal_node" not in st.session_state
    or st.session_state.goal_node not in graph
):
    nodes_list = list(graph.nodes())
    goal_index = min(150, len(nodes_list) - 1)
    st.session_state.goal_node = nodes_list[goal_index]


# ============================================================
# PROCESS START LOCATION SEARCH
# ============================================================

if submit_start and start_input.strip():
    coords = geocode_place_name(start_input.strip())

    if coords:
        start_lat = coords[0]
        start_lon = coords[1]
        nearest_node = find_nearest_node_custom(
            graph,
            start_lat,
            start_lon
        )
        st.session_state.start_node = nearest_node
        st.sidebar.success("Found Start Location!")
    else:
        st.sidebar.error("Start location not found.")


# ============================================================
# PROCESS DESTINATION SEARCH
# ============================================================

if submit_dest and dest_input.strip():
    coords = geocode_place_name(dest_input.strip())

    if coords:
        dest_lat = coords[0]
        dest_lon = coords[1]
        nearest_node = find_nearest_node_custom(
            graph,
            dest_lat,
            dest_lon
        )
        st.session_state.goal_node = nearest_node
        st.sidebar.success("Found Destination Location!")
    else:
        st.sidebar.error("Destination location not found.")


# ============================================================
# CREATE ACTIVE GRAPH + APPLY EXISTING HAZARDS
# ============================================================

active_graph = graph.copy()

for hz_node, hz_type in st.session_state.hazard_history:
    if hz_node in active_graph:
        apply_hazard(
            active_graph,
            hz_node,
            hz_type,
            depth=2
        )


# ============================================================
# CALCULATE OPTIMAL ROUTE
# ============================================================

path, cost, waypoints, exec_time = calculate_route(
    active_graph,
    st.session_state.start_node,
    st.session_state.goal_node,
    agent_mode=agent_mode,
    algorithm=algorithm,
)


# ============================================================
# TOP METRICS
# ============================================================

render_metrics(algorithm, cost, waypoints, exec_time)


# ============================================================
# MAP TITLE
# ============================================================

st.subheader(
    f"Interactive Map Area — {st.session_state.location_name}"
)

st.info(
    f"💡 **Current Click Mode:** `{selection_mode}`. "
    f"Click anywhere directly on the map to interact."
)


# ============================================================
# GENERATE + DISPLAY MAP
# ============================================================

map_obj = generate_map_view(
    active_graph,
    path,
    st.session_state.start_node,
    st.session_state.goal_node,
    hazard_locations=st.session_state.hazard_history,
    theme_key=theme_key,
)

map_data = st_folium(
    map_obj,
    width=1200,
    height=600,
    key="interactive_map"
)


# ============================================================
# HANDLE MAP CLICK
# ============================================================

if map_data and map_data.get("last_clicked"):
    click_coords = (
        map_data["last_clicked"]["lat"],
        map_data["last_clicked"]["lng"]
    )

    if click_coords != st.session_state.last_processed_click:
        st.session_state.last_processed_click = click_coords

        nearest_node = find_nearest_node_custom(
            active_graph,
            click_coords[0],
            click_coords[1]
        )

        if "Start" in selection_mode:
            st.session_state.start_node = nearest_node

        elif "Destination" in selection_mode:
            st.session_state.goal_node = nearest_node

        elif "Hazard" in selection_mode:
            st.session_state.hazard_history.append(
                (nearest_node, hazard_tool)
            )

        st.rerun()
