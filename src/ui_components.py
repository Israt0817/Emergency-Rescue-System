import streamlit as st

from config.settings import THEMES


def render_location_settings():
    st.sidebar.title("🚨 Emergency Routing Panel")
    st.sidebar.subheader("📍 Location Settings")

    with st.sidebar.form(key="location_form"):
        entered_location = st.text_input(
            "Enter Your Location",
            placeholder="e.g. Mirpur 10, Dhaka"
        )
        submit_location = st.form_submit_button("Set Location")

    refresh_map = st.sidebar.button("🔄 Refresh Map")
    return entered_location, submit_location, refresh_map


def render_interaction_controls():
    st.sidebar.markdown("---")
    st.sidebar.subheader("🎯 Map Interaction Mode")

    selection_mode = st.sidebar.radio(
        "Active Map Click Mode:",
        [
            "🟢 Set Start Point",
            "🔴 Set Destination Point",
            "⚠️ Apply Hazard On Map",
        ],
        help="Select an action and click anywhere on the map.",
    )

    hazard_tool = "blocked"
    clear_hazards = False

    if "Hazard" in selection_mode:
        hazard_tool = st.sidebar.selectbox(
            "Active Hazard Brush Type",
            ["blocked", "fire", "traffic", "smoke"],
            help=(
                "Selected hazard type will be applied "
                "when you click on the map."
            ),
        )
        clear_hazards = st.sidebar.button("🧹 Clear All Hazards")

    return selection_mode, hazard_tool, clear_hazards


def render_route_search_controls():
    st.sidebar.markdown("---")
    st.sidebar.markdown("**🟢 Search Start Location**")

    with st.sidebar.form(key="start_form"):
        start_input = st.text_input(
            "Start Location Name",
            placeholder="e.g. Farmgate, Dhaka"
        )
        submit_start = st.form_submit_button("Set Start Location")

    st.sidebar.markdown("**🔴 Search Destination Location**")

    with st.sidebar.form(key="dest_form"):
        dest_input = st.text_input(
            "Destination Location Name",
            placeholder="e.g. Tejgaon, Dhaka"
        )
        submit_dest = st.form_submit_button("Set Destination Location")

    return start_input, submit_start, dest_input, submit_dest


def render_routing_settings():
    st.sidebar.markdown("---")

    agent_mode = st.sidebar.selectbox(
        "Agent Mode",
        ["Ambulance", "Firefighter"]
    )

    algorithm = st.sidebar.radio(
        "Algorithm",
        ["A*", "Dijkstra"]
    )

    theme_key = st.sidebar.selectbox(
        "Map Theme",
        list(THEMES.keys())
    )

    return agent_mode, algorithm, theme_key


def render_metrics(algorithm, cost, waypoints, exec_time):
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Selected Algorithm", algorithm)
    col2.metric(
        "Path Cost",
        f"{cost:.2f} m" if cost != float("inf") else "Blocked / No Path"
    )
    col3.metric("Waypoints", waypoints)
    col4.metric("Compute Time", f"{exec_time:.2f} ms")
