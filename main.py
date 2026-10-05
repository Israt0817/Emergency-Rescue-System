import streamlit as st
from streamlit_folium import st_folium
import math
import copy
import requests
import time
from src.map_utils import (
    load_graph_network,
    apply_hazard,
    generate_map_view,
    geocode_place_name,
)
from src.algorithm import calculate_route
from config.settings import THEMES

st.set_page_config(layout="wide", page_title="AI Emergency Rescue System")

# Inject Cyberpunk Neon Cyan CSS & Animated Splash Page Styling
st.markdown(
    """
<style>
    /* Main Background with Deep Midnight Blue / Cyan Gradient */
    .stApp {
        background: radial-gradient(circle at 80% 20%, #05192D 0%, #0B1118 60%, #03070C 100%) !important;
        color: #FAFAFA !important;
    }
    
    /* Sidebar Dark Styling with Cyan Tint */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #091522 0%, #060A0F 100%) !important;
        border-right: 1px solid #112A45 !important;
    }

    /* Modern Metric Cards with Glowing Electric Cyan Border Animation */
    [data-testid="stMetric"] {
        background-color: #071320 !important;
        border: 1px solid #00E5FF !important;
        padding: 15px !important;
        border-radius: 12px !important;
        box-shadow: 0 0 18px rgba(0, 229, 255, 0.25) !important;
        animation: cardGlow 2.5s infinite alternate !important;
    }
    
    [data-testid="stMetricLabel"] {
        color: #90CAF9 !important;
        font-weight: 500 !important;
    }

    [data-testid="stMetricValue"] {
        color: #FFFFFF !important;
        text-shadow: 0 0 12px rgba(0, 229, 255, 0.7) !important;
    }

    /* Pulsing Alert Banner Style */
    .stAlert {
        background-color: #0A192F !important;
        border: 1px solid #00B0FF !important;
        color: #E1F5FE !important;
        border-radius: 10px !important;
        box-shadow: 0 0 12px rgba(0, 176, 255, 0.25) !important;
    }

    /* Animated Blinking Glowing Keyframes for Cyan Theme */
    @keyframes cardGlow {
        0% {
            border-color: rgba(0, 229, 255, 0.3);
            box-shadow: 0 0 8px rgba(0, 229, 255, 0.15);
        }
        50% {
            border-color: rgba(0, 229, 255, 0.85);
            box-shadow: 0 0 22px rgba(0, 229, 255, 0.45);
        }
        100% {
            border-color: rgba(132, 255, 255, 1);
            box-shadow: 0 0 30px rgba(132, 255, 255, 0.7);
        }
    }

    @keyframes emergencyPulse {
        0% {
            box-shadow: 0 0 0 0 rgba(0, 229, 255, 0.8);
        }
        70% {
            box-shadow: 0 0 0 14px rgba(0, 229, 255, 0);
        }
        100% {
            box-shadow: 0 0 0 0 rgba(0, 229, 255, 0);
        }
    }

    /* Electric Cyan Glowing Buttons */
    .stButton>button {
        background: linear-gradient(135deg, #0091EA 0%, #01579B 100%) !important;
        color: #FFFFFF !important;
        border: 1px solid #00E5FF !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton>button:hover {
        background: linear-gradient(135deg, #00B0FF 0%, #0288D1 100%) !important;
        animation: emergencyPulse 1.2s infinite !important;
        border: 1px solid #84FFFF !important;
    }

    /* Splash Screen Styling */
    .splash-title {
        font-size: 3.2rem;
        font-weight: 800;
        text-align: center;
        color: #FFFFFF;
        text-shadow: 0 0 20px #00E5FF, 0 0 40px #00B0FF;
        margin-top: 100px;
        margin-bottom: 10px;
        animation: splashGlow 2s infinite alternate;
    }

    .splash-subtitle {
        font-size: 1.2rem;
        text-align: center;
        color: #84FFFF;
        margin-bottom: 40px;
        letter-spacing: 2px;
    }

    .splash-footer {
        text-align: center;
        font-size: 1.4rem;
        font-weight: 700;
        color: #00E5FF;
        letter-spacing: 3px;
        margin-top: 50px;
        text-shadow: 0 0 10px rgba(0, 229, 255, 0.8);
        text-transform: uppercase;
    }

    @keyframes splashGlow {
        0% { text-shadow: 0 0 10px #00E5FF, 0 0 20px #00B0FF; }
        100% { text-shadow: 0 0 25px #84FFFF, 0 0 50px #00E5FF; }
    }
</style>
""",
    unsafe_allow_html=True,
)

# Session State for Initial Loading Screen
if "splash_loaded" not in st.session_state:
    st.session_state.splash_loaded = False

# Render Loading Welcome Screen on first launch
if not st.session_state.splash_loaded:
    st.markdown(
        '<div class="splash-title">🚨 AI EMERGENCY RESCUE SYSTEM</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="splash-subtitle">INITIALIZING COMMAND MATRIX & ROUTING ENGINES...</div>',
        unsafe_allow_html=True,
    )

    progress_bar = st.progress(0)
    status_text = st.empty()

    loading_steps = [
        "Connecting to Geolocation API...",
        "Calibrating Neural Pathfinding Algorithms...",
        "Loading Topographic Map Networks...",
        "Arming Real-Time Hazard Sensors...",
        "System Ready.",
    ]

    for idx, step in enumerate(loading_steps):
        status_text.markdown(
            f"<p style='text-align: center; color: #90CAF9;'>{step}</p>",
            unsafe_allow_html=True,
        )
        time.sleep(0.4)
        progress_bar.progress((idx + 1) * 20)

    st.markdown(
        '<div class="splash-footer">⚡ Invented by Team X ⚡</div>',
        unsafe_allow_html=True,
    )
    time.sleep(1.2)

    st.session_state.splash_loaded = True
    st.rerun()


@st.cache_data
def get_live_location():
    try:
        response = requests.get("https://ipapi.co/json/", timeout=2)
        if response.status_code == 200:
            data = response.json()
            city = data.get("city")
            country = data.get("country_name")
            if city and country:
                return f"{city}, {country}"
    except Exception:
        pass
    return "Dhaka, Bangladesh"


if "location_name" not in st.session_state:
    st.session_state.location_name = get_live_location()

if "hazard_history" not in st.session_state:
    st.session_state.hazard_history = []

# Sidebar UI
st.sidebar.title("🚨 Emergency Routing Panel")

st.sidebar.subheader("📍 Location Settings")

with st.sidebar.form(key="global_search_form"):
    global_search = st.text_input(
        "Enter Location:",
        value=st.session_state.location_name,
        placeholder="e.g. New York, Tokyo, Khulna",
    )
    submit_search = st.form_submit_button("Search Location")

if submit_search and global_search.strip():
    if global_search.strip() != st.session_state.location_name:
        st.session_state.location_name = global_search.strip()
        st.session_state.pop("start_node", None)
        st.session_state.pop("goal_node", None)
        st.session_state.hazard_history = []
        st.rerun()

if st.sidebar.button("🔄 Refresh Map"):
    st.cache_data.clear()
    st.session_state.hazard_history = []
    st.rerun()

# Load Base Graph Network
with st.spinner(f"Loading map network for {st.session_state.location_name}..."):
    graph = load_graph_network(st.session_state.location_name)
    nodes = list(graph.nodes())


def find_nearest_node_custom(G, lat, lon):
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

# Conditional display: Hazard options appear only when "Apply Hazard On Map" is selected
if "Hazard" in selection_mode:
    hazard_tool = st.sidebar.selectbox(
        "Active Hazard Brush Type",
        ["blocked", "fire", "traffic", "smoke"],
        help="Selected hazard type will be applied when you click on the map.",
    )

    if st.sidebar.button("🧹 Clear All Hazards"):
        st.cache_data.clear()
        st.session_state.hazard_history = []
        st.rerun()
else:
    hazard_tool = "blocked"  # default fallback value

st.sidebar.markdown("---")
agent_mode = st.sidebar.selectbox("Agent Mode", ["Ambulance", "Firefighter"])
algorithm = st.sidebar.radio("Algorithm", ["A*", "Dijkstra"])
theme_key = st.sidebar.selectbox("Map Theme", list(THEMES.keys()))

active_graph = copy.deepcopy(graph)

for hz_node, hz_type in st.session_state.hazard_history:
    apply_hazard(active_graph, hz_node, hz_type, depth=3)

path, cost, waypoints, exec_time = calculate_route(
    active_graph,
    st.session_state.start_node,
    st.session_state.goal_node,
    agent_mode=agent_mode,
    algorithm=algorithm,
)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Selected Algorithm", algorithm)
col2.metric("Path Cost", f"{cost:.2f} m" if cost < 1e7 else "Blocked / No Path")
col3.metric("Waypoints", waypoints)
col4.metric("Compute Time", f"{exec_time:.2f} ms")

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

# Full width map layout
map_data = st_folium(map_obj, width="100%", height=600, key="interactive_map")

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

# Footer credit at bottom of sidebar
st.sidebar.markdown("---")
st.sidebar.caption("⚡ **Invented by Team X**")
