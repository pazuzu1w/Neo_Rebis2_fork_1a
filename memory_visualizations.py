# memory_visualization.py
import networkx as nx
import matplotlib.pyplot as plt
from io import BytesIO
import base64


class MemoryVisualizer:
    def __init__(self, memory_manager):
        self.memory_manager = memory_manager

    def generate_memory_graph(self, central_query, depth=2, max_connections=20):
        """Generate a graph visualization of related memories"""
        G = nx.Graph()

        # Start with central query
        central_memories = self.memory_manager.search_all_memories(central_query, n_results=5)

        # Add central nodes
        for memory in central_memories:
            G.add_node(memory["id"], text=memory["text"][:50] + "...",
                       type=memory["metadata"].get("memory_type", "unknown"))

        # Expand graph for each depth level
        current_ids = [memory["id"] for memory in central_memories]

        for _ in range(depth):
            next_ids = []
            for memory_id in current_ids:
                memory = self.memory_manager.get_memory_by_id(memory_id)
                if not memory:
                    continue

                # Find related memories
                related = self.memory_manager.search_all_memories(memory["text"], n_results=3)

                for related_memory in related:
                    if related_memory["id"] != memory_id:  # Avoid self-connections
                        # Add node if not exists
                        if related_memory["id"] not in G:
                            G.add_node(related_memory["id"],
                                       text=related_memory["text"][:50] + "...",
                                       type=related_memory["metadata"].get("memory_type", "unknown"))

                        # Add edge with similarity as weight
                        similarity = 1.0 - (related_memory.get("distance", 0.5) or 0.5)
                        G.add_edge(memory_id, related_memory["id"], weight=similarity)

                        next_ids.append(related_memory["id"])

                        # Limit connections
                        if len(G.edges) >= max_connections:
                            break

            current_ids = next_ids

        return G

    def visualize_graph(self, graph, filename=None):
        """Create a visualization of the memory graph"""
        plt.figure(figsize=(12, 8))

        # Create position layout
        pos = nx.spring_layout(graph)

        # Node colors based on type
        color_map = {
            "episodic": "blue",
            "semantic": "green",
            "procedural": "red",
            "consolidated_episodic": "purple",
            "unknown": "gray"
        }

        node_colors = [color_map.get(graph.nodes[node]["type"], "gray") for node in graph.nodes]

        # Draw the graph
        nx.draw_networkx_nodes(graph, pos, node_color=node_colors, alpha=0.8, node_size=300)

        # Edge weights for thickness
        edge_weights = [graph[u][v]["weight"] * 5 for u, v in graph.edges]
        nx.draw_networkx_edges(graph, pos, width=edge_weights, alpha=0.5)

        # Add labels
        labels = {node: graph.nodes[node]["text"] for node in graph.nodes}
        nx.draw_networkx_labels(graph, pos, labels, font_size=8)

        plt.title("Memory Connections Visualization")
        plt.axis("off")

        if filename:
            plt.savefig(filename)
            return filename
        else:
            # Return as base64 for embedding in UI
            buffer = BytesIO()
            plt.savefig(buffer, format="png")
            plt.close()
            buffer.seek(0)
            image_png = buffer.getvalue()
            buffer.close()
            return base64.b64encode(image_png).decode("utf-8")