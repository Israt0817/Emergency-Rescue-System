import streamlit as st
from streamlit_folium import st_folium
import math
from src.map_utils import (
    load_graph_network,
    apply_hazard,
    generate_map_view,
    geocode_place_name,
)
from src.algorithm import calculate_route
from config.settings import THEMES, DEFAULT_LOCATION, CITY_COORDINATES

st.set_page_config(layout="wide", page_title="AI Emergency Rescue System")

CITY_PRESETS = list(CITY_COORDINATES.keys())

if "location_name" not in st.session_state:
    st.session_state.location_name = DEFAULT_LOCATION

# Track active hazard markers placed on graph
if "hazard_history" not in st.session_state:
    st.session_state.hazard_history = []

# Sidebar UI
st.sidebar.title("🚨 Emergency Routing Panel")

st.sidebar.subheader("📍 Location Settings")
selected_city = st.sidebar.selectbox("Select City", CITY_PRESETS, index=0)
custom_city = st.sidebar.text_input("Or enter custom location", value="")

target_city = custom_city.strip() if custom_city.strip() else selected_city

if target_city != st.session_state.location_name:
    st.session_state.location_name = target_city
    st.session_state.pop("start_node", None)
    st.session_state.pop("goal_node", None)
    st.session_state.hazard_history = []

if st.sidebar.button("🔄 Refresh Map"):
    st.cache_data.clear()
    st.session_state.hazard_history = []
    st.rerun()

# Load Base Graph Network
with st.spinner(f"Loading map network for {st.session_state.location_name}..."):
    graph = load_graph_network(st.session_state.location_name)
    nodes = list(graph.nodes())


def find_nearest_node_custom(G, lat, lon):
    """Finds the closest node in graph to clicked/geocoded lat/lon coordinates."""
    min_dist = float("inf")
    best_node = list(G.nodes())[0]
    for node, data in G.nodes(data=True):
        if "y" in data and "x" in data:
            dist = math.hypot(data["y"] - lat, data["x"] - lon)
            if dist < min_dist:
                min_dist = dist
                best_node = node
    return best_node


max_idx = len(nodes) - 1
if "start_node" not in st.session_state or st.session_state.start_node not in graph:
    st.session_state.start_node = nodes[min(10, max_idx)]
if "goal_node" not in st.session_state or st.session_state.goal_node not in graph:
    st.session_state.goal_node = nodes[min(150, max_idx)]

if "last_processed_click" not in st.session_state:
    st.session_state.last_processed_click = None

st.sidebar.markdown("---")
st.sidebar.subheader("🎯 Map Interaction Mode")

selection_mode = st.sidebar.radio(
    "Active Map Click Mode:",
    ["🟢 Set Start Point", "🔴 Set Destination Point", "⚠️ Apply Hazard On Map"],
    help="Select an action and click anywhere on the map.",
)

hazard_tool = st.sidebar.selectbox(
    "Active Hazard Brush Type",
    ["blocked", "fire", "traffic", "smoke"],
    help="Selected hazard type will be applied when you click on the map.",
)

if st.sidebar.button("🧹 Clear All Hazards"):
    st.cache_data.clear()
    st.session_state.hazard_history = []
    st.rerun()

# Text Search Form for Start Point
st.sidebar.markdown("---")
st.sidebar.markdown("**🟢 Search Start Location**")
with st.sidebar.form(key="start_form"):
    start_input = st.text_input(
        "Start Location Name", placeholder="e.g. Farmgate, Dhaka"
    )
    submit_start = st.form_submit_button("Set Start Location")
    if submit_start and start_input.strip():
        coords = geocode_place_name(start_input.strip())
        if coords:
            st.session_state.start_node = find_nearest_node_custom(
                graph, coords[0], coords[1]
            )
            st.sidebar.success("Found Start Location!")
            st.rerun()
        else:
            st.sidebar.error("Location not found.")

# Text Search Form for Destination Point
st.sidebar.markdown("**🔴 Search Destination Location**")
with st.sidebar.form(key="dest_form"):
    dest_input = st.text_input(
        "Destination Location Name", placeholder="e.g. Tejgaon, Dhaka"
    )
    submit_dest = st.form_submit_button("Set Destination Location")
    if submit_dest and dest_input.strip():
        coords = geocode_place_name(dest_input.strip())
        if coords:
            st.session_state.goal_node = find_nearest_node_custom(
                graph, coords[0], coords[1]
            )
            st.sidebar.success("Found Destination Location!")
            st.rerun()
        else:
            st.sidebar.error("Location not found.")

st.sidebar.markdown("---")
agent_mode = st.sidebar.selectbox("Agent Mode", ["Ambulance", "Firefighter"])
algorithm = st.sidebar.radio("Algorithm", ["A*", "Dijkstra"])
theme_key = st.sidebar.selectbox("Map Theme", list(THEMES.keys()))

# Create a fresh graph copy to apply hazards without caching conflicts
active_graph = graph.copy()

# Apply all accumulated hazards to the active graph network
for hz_node, hz_type in st.session_state.hazard_history:
    apply_hazard(active_graph, hz_node, hz_type, depth=2)

# Calculate Path
path, cost, waypoints, exec_time = calculate_route(
    active_graph,
    st.session_state.start_node,
    st.session_state.goal_node,
    agent_mode=agent_mode,
    algorithm=algorithm,
)

# Render Metrics Header
col1, col2, col3, col4 = st.columns(4)
col1.metric("Selected Algorithm", algorithm)
col2.metric(
    "Path Cost", f"{cost:.2f} m" if cost != float("inf") else "Blocked / No Path"
)
col3.metric("Waypoints", waypoints)
col4.metric("Compute Time", f"{exec_time:.2f} ms")

# Render Interactive Map
st.subheader(f"Interactive Map Area — {st.session_state.location_name}")
st.info(
    f"💡 **Current Click Mode:** `{selection_mode}`. Click anywhere directly on the map to interact."
)

map_obj = generate_map_view(
    active_graph,
    path,
    st.session_state.start_node,
    st.session_state.goal_node,
    hazard_locations=st.session_state.hazard_history,
    theme_key=theme_key,
)

# Render Folium map and handle map click events
map_data = st_folium(map_obj, width=1200, height=600, key="interactive_map")

if map_data and map_data.get("last_clicked"):
    click_coords = (map_data["last_clicked"]["lat"], map_data["last_clicked"]["lng"])

    if click_coords != st.session_state.last_processed_click:
        st.session_state.last_processed_click = click_coords
        nearest_node = find_nearest_node_custom(
            active_graph, click_coords[0], click_coords[1]
        )

        if "Start" in selection_mode:
            st.session_state.start_node = nearest_node
        elif "Destination" in selection_mode:
            st.session_state.goal_node = nearest_node
        elif "Hazard" in selection_mode:
            st.session_state.hazard_history.append((nearest_node, hazard_tool))

        st.rerun()
