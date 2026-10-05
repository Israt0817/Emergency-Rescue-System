import math

def euclidean_heuristic(G, u, goal_node):
    """Euclidean distance heuristic for A* in meters."""
    x1, y1 = G.nodes[u]["x"], G.nodes[u]["y"]
    x2, y2 = G.nodes[goal_node]["x"], G.nodes[goal_node]["y"]
    return math.hypot(x1 - x2, y1 - y2) * 111000.0

def find_nearest_node_custom(G, lat, lon):
    min_dist = float("inf")
    best_node = list(G.nodes())[0]

    for node, data in G.nodes(data=True):
        if "y" in data and "x" in data:
            dist = math.hypot(
                data["y"] - lat,
                data["x"] - lon
            )

            if dist < min_dist:
                min_dist = dist
                best_node = node

    return best_node
