import osmnx as ox
import folium
import streamlit as st
import networkx as nx
import requests
from config.settings import DEFAULT_LOCATION, THEMES, CITY_COORDINATES


@st.cache_data(show_spinner=False)
def load_graph_network(location_name=DEFAULT_LOCATION):
    # 1. Resolve location name to coordinates first (handles custom worldwide text search)
    coords = None
    if location_name in CITY_COORDINATES:
        coords = CITY_COORDINATES[location_name]
    else:
        # Dynamically geocode any searched place worldwide using Nominatim
        coords = geocode_place_name(location_name)

    base_lat, base_lon = coords if coords else (23.777172, 90.399452)

    try:
        ox.settings.timeout = 10
        # 2. Fetch graph using the resolved lat/lon point and radius
        G = ox.graph_from_point((base_lat, base_lon), dist=2000, network_type="drive")
    except Exception:
        grid = nx.grid_2d_graph(25, 25)
        G = nx.MultiDiGraph()

        mapping = {}
        for idx, (r, c) in enumerate(grid.nodes()):
            mapping[(r, c)] = idx
            G.add_node(
                idx, y=base_lat + ((r - 12) * 0.002), x=base_lon + ((c - 12) * 0.002)
            )

        for u, v in grid.edges():
            u_id, v_id = mapping[u], mapping[v]
            G.add_edge(u_id, v_id, length=100.0, hazard="normal")
            G.add_edge(v_id, u_id, length=100.0, hazard="normal")

    for u, v, k, data in G.edges(keys=True, data=True):
        if "hazard" not in data:
            data["hazard"] = "normal"

    return G


def geocode_place_name(query):
    """Reliable fallback geocoder using Nominatim API directly."""
    try:
        url = (
            f"https://nominatim.openstreetmap.org/search?q={query}&format=json&limit=1"
        )
        headers = {"User-Agent": "EmergencyRoutingApp/1.0"}
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data:
                return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception:
        pass
    return None


def apply_hazard(G, center_node, hazard_type, depth=1):
    visited = set()
    queue = [(center_node, 0)]

    while queue:
        curr, dist = queue.pop(0)
        if curr in visited or dist > depth:
            continue
        visited.add(curr)

        for nbr in G.successors(curr):
            for k in G[curr][nbr]:
                G[curr][nbr][k]["hazard"] = hazard_type
            if dist < depth:
                queue.append((nbr, dist + 1))

        for pred in G.predecessors(curr):
            for k in G[pred][curr]:
                G[pred][curr][k]["hazard"] = hazard_type
            if dist < depth:
                queue.append((pred, dist + 1))


def generate_map_view(
    G, path, start_node, goal_node, hazard_locations=None, theme_key="OpenStreetMap"
):
    theme = THEMES.get(theme_key, THEMES["OpenStreetMap"])

    start_lat = G.nodes[start_node]["y"]
    start_lon = G.nodes[start_node]["x"]

    if "attr" in theme:
        m = folium.Map(
            location=[start_lat, start_lon],
            zoom_start=14,
            tiles=theme["tiles"],
            attr=theme["attr"],
        )
    else:
        m = folium.Map(
            location=[start_lat, start_lon], zoom_start=14, tiles=theme["tiles"]
        )

    hazard_colors = {
        "traffic": "#FFA726",
        "smoke": "#78909C",
        "fire": "#E53935",
        "blocked": "#212121",
    }

    # Render hazard-affected road segments
    for u, v, k, data in G.edges(keys=True, data=True):
        hz = data.get("hazard", "normal")
        if hz != "normal":
            p1 = (G.nodes[u]["y"], G.nodes[u]["x"])
            p2 = (G.nodes[v]["y"], G.nodes[v]["x"])
            folium.PolyLine(
                [p1, p2], color=hazard_colors.get(hz, "#000000"), weight=8, opacity=0.8
            ).add_to(m)

    # Render optimal route
    if path:
        route_coords = [(G.nodes[node]["y"], G.nodes[node]["x"]) for node in path]
        folium.PolyLine(
            route_coords, color=theme["route_color"], weight=6, opacity=0.9
        ).add_to(m)

    # Markers
    folium.Marker(
        [start_lat, start_lon],
        popup="Start Location",
        icon=folium.Icon(color="green", icon="play"),
    ).add_to(m)
    goal_lat, goal_lon = G.nodes[goal_node]["y"], G.nodes[goal_node]["x"]
    folium.Marker(
        [goal_lat, goal_lon],
        popup="Emergency Destination",
        icon=folium.Icon(color="red", icon="stop"),
    ).add_to(m)

    # Draw hazard markers placed by user clicks
    if hazard_locations:
        for hz_node, hz_type in hazard_locations:
            h_lat, h_lon = G.nodes[hz_node]["y"], G.nodes[hz_node]["x"]
            icon_color = (
                "orange"
                if hz_type == "traffic"
                else ("red" if hz_type == "fire" else "black")
            )
            folium.Marker(
                [h_lat, h_lon],
                popup=f"Hazard: {hz_type.upper()}",
                icon=folium.Icon(color=icon_color, icon="warning", prefix="fa"),
            ).add_to(m)

    return m
