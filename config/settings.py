# System Configuration and Hazard Definitions

HAZARD_WEIGHTS = {
    "normal": 1.0,
    "traffic": 50.0,
    "smoke": 200.0,
    "fire": 1000.0,
    "blocked": float("inf"),
}

DEFAULT_LOCATION = "Dhaka, Bangladesh"

CITY_COORDINATES = {
    "Dhaka, Bangladesh": (23.777172, 90.399452),
    "Manhattan, New York, USA": (40.7831, -73.9712),
    "London, UK": (51.5074, -0.1278),
    "Tokyo, Japan": (35.6762, 139.6503),
}

THEMES = {
    "OpenStreetMap": {
        "tiles": "OpenStreetMap",
        "route_color": "#0000FF",
        "start_color": "#00FF00",
        "goal_color": "#FF0000",
    },
    "Esri Satellite": {
        "tiles": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        "attr": "Esri",
        "route_color": "#FFD700",
        "start_color": "#00FF00",
        "goal_color": "#FF0055",
    },
    "Carto Light": {
        "tiles": "https://a.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png",
        "attr": "&copy; <a href='https://www.openstreetmap.org/copyright'>OpenStreetMap</a> contributors &copy; <a href='https://carto.com/attributions'>CARTO</a>",
        "route_color": "#6200EE",
        "start_color": "#2E7D32",
        "goal_color": "#C62828",
    },
}
