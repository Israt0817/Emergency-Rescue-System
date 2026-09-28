import networkx as nx
import time
import math

HAZARD_PENALTIES = {
    "normal": 1.0,
    "traffic": 10.0,
    "smoke": 50.0,
    "fire": 1000.0,
    "blocked": 1_000_000_000.0,  # Extremely high penalty to force full detour
}


def get_edge_weight(u, v, data, agent_mode="Ambulance"):
    """Evaluates edge weight considering hazard penalties."""
    base_length = data.get("length", 100.0)
    hazard = data.get("hazard", "normal")

    penalty = HAZARD_PENALTIES.get(hazard, 1.0)
    if agent_mode == "Firefighter" and hazard == "fire":
        penalty = 2.0

    return base_length * penalty


def euclidean_heuristic(G, u, goal_node):
    """Euclidean distance heuristic for A* in meters."""
    x1, y1 = G.nodes[u]["x"], G.nodes[u]["y"]
    x2, y2 = G.nodes[goal_node]["x"], G.nodes[goal_node]["y"]
    return math.hypot(x1 - x2, y1 - y2) * 111000.0


def calculate_route(
    graph, start_node, goal_node, agent_mode="Ambulance", algorithm="A*"
):
    """Calculates route with guaranteed hazard avoidance for A* and Dijkstra."""
    start_time = time.time()

    # NetworkX weight accessor supporting MultiDiGraph edge dictionaries
    def weight_func(u, v, d):
        if isinstance(d, dict) and any(isinstance(k, int) for k in d.keys()):
            return min(
                get_edge_weight(u, v, edge_data, agent_mode) for edge_data in d.values()
            )
        return get_edge_weight(u, v, d, agent_mode)

    try:
        if algorithm == "A*":
            path = nx.astar_path(
                graph,
                start_node,
                goal_node,
                heuristic=lambda u, v: euclidean_heuristic(graph, u, goal_node),
                weight=weight_func,
            )
        else:
            path = nx.dijkstra_path(graph, start_node, goal_node, weight=weight_func)

        # Calculate total cost of the path
        cost = 0.0
        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            edge_data = graph.get_edge_data(u, v)
            if edge_data:
                cost += min(
                    get_edge_weight(u, v, ed, agent_mode) for ed in edge_data.values()
                )

        waypoints = len(path)

    except (nx.NetworkXNoPath, nx.NodeNotFound):
        path = []
        cost = float("inf")
        waypoints = 0

    exec_time = (time.time() - start_time) * 1000.0

    return path, cost, waypoints, exec_time
