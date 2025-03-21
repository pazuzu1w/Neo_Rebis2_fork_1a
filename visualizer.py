import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
import networkx as nx
from PyQt6.QtWidgets import QWidget, QVBoxLayout
import numpy as np
from memory import MemoryManager


class MemoryVisualizer(QWidget):
    def __init__(self, memory_manager):
        super().__init__()
        self.memory_manager = memory_manager
        self.setup_ui()

    def setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.figure = plt.figure(figsize=(8, 6), facecolor='#2D2D2D')
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.layout.addWidget(self.canvas)
        self.setWindowTitle("Memory Network")

    def generate_network_graph(self, max_memories=50):
        # Clear the figure
        self.figure.clear()

        # Create a graph
        G = nx.Graph()

        # Get recent conversations
        conversations = self.memory_manager.get_conversation_history(limit=max_memories)

        # Create nodes for each conversation
        for i, convo in enumerate(conversations):
            # Add the conversation as a node
            G.add_node(f"C{i}", type="conversation", text=convo.get("user_message", "")[:30])

            # Get topics from metadata
            metadata = convo.get("metadata", {})
            topics = [v for k, v in metadata.items() if k.startswith("topic_")]

            # Add topic nodes and edges
            for topic in topics:
                if not G.has_node(topic):
                    G.add_node(topic, type="topic")
                G.add_edge(f"C{i}", topic)

        # Create the plot
        ax = self.figure.add_subplot(111)
        ax.set_facecolor('#2D2D2D')

        # Set node colors based on type
        node_colors = ['#E94560' if G.nodes[node].get('type') == 'conversation' else '#3F72AF'
                       for node in G.nodes()]

        # Draw the network
        pos = nx.spring_layout(G)
        nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=700, alpha=0.8, ax=ax)
        nx.draw_networkx_edges(G, pos, width=1.0, alpha=0.5, ax=ax)
        nx.draw_networkx_labels(G, pos, font_size=10, font_color='white', ax=ax)

        # Remove axis
        ax.set_axis_off()

        # Update canvas
        self.canvas.draw()

    def generate_topic_heatmap(self, top_n=15):
        # Clear the figure
        self.figure.clear()

        # Get all memories
        all_topics = {}
        memories = self.memory_manager.collection.get()

        # Count topic frequencies
        for metadata in memories.get("metadatas", []):
            if metadata:
                for key, value in metadata.items():
                    if key.startswith("topic_"):
                        all_topics[value] = all_topics.get(value, 0) + 1

        # Get top N topics
        top_topics = sorted(all_topics.items(), key=lambda x: x[1], reverse=True)[:top_n]

        # Create plot
        ax = self.figure.add_subplot(111)
        ax.set_facecolor('#2D2D2D')

        topics, counts = zip(*top_topics) if top_topics else ([], [])
        y_pos = np.arange(len(topics))

        # Create horizontal bar chart
        bars = ax.barh(y_pos, counts, align='center', color='#3F72AF')
        ax.set_yticks(y_pos)
        ax.set_yticklabels(topics, fontsize=10, color='white')
        ax.invert_yaxis()  # Labels read top-to-bottom
        ax.set_xlabel('Frequency', color='white')
        ax.set_title('Top Topics in Your Memory Network', color='white')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_color('white')
        ax.spines['left'].set_color('white')
        ax.tick_params(axis='x', colors='white')

        # Add count labels
        for i, bar in enumerate(bars):
            width = bar.get_width()
            ax.text(width + 0.5, bar.get_y() + bar.get_height() / 2,
                    f'{width:.0f}', ha='left', va='center', color='white')

        # Update canvas
        self.canvas.draw()