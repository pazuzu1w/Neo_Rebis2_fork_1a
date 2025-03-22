# memory_component.py
from component import Component
from memory import MemoryManager
from memory_consolidation import MemoryConsolidator
from memory_importance import MemoryImportanceScorer
from memory_visualizations import MemoryVisualizer
from memory_pruning import MemoryPruner
from conversation_threading import ThreadManager


class MemoryComponent(Component):
    def __init__(self, persist_directory="./chroma_db"):
        super().__init__("memory")
        self.persist_directory = persist_directory

        # Core memory components
        self.memory_manager = None
        self.importance_scorer = None
        self.consolidator = None
        self.visualizer = None
        self.pruner = None
        self.thread_manager = None

        # Settings
        self.auto_consolidation = True
        self.auto_pruning = True
        self.consolidation_days = 30
        self.pruning_days = 90
        self.importance_threshold = 30

    def initialize(self):
        """Initialize the memory component and all subcomponents"""
        # Get the logger from the engine
        self.logger = self.engine.get_component("logger")
        if not self.logger:
            # Fallback to basic logging
            import logging
            self.logger = logging.getLogger("memory_component")

        self.logger.info("Initializing Memory Component")

        # Initialize the memory manager
        self.memory_manager = MemoryManager(self.persist_directory)

        # Get model interface from engine
        self.model_interface = self.engine.get_component("model")
        if not self.model_interface:
            self.logger.warning("Model interface not found, some memory features will be limited")

        # Initialize subcomponents that need the model interface
        if self.model_interface:
            self.importance_scorer = MemoryImportanceScorer(self.memory_manager, self.model_interface)
            self.consolidator = MemoryConsolidator(self.memory_manager, self.model_interface)

        # Initialize visualization and pruning
        self.visualizer = MemoryVisualizer(self.memory_manager)

        if self.importance_scorer:
            self.pruner = MemoryPruner(self.memory_manager, self.importance_scorer)

        # Initialize thread manager
        self.thread_manager = ThreadManager(self.memory_manager)

        # Register maintenance tasks (if scheduler available)
        scheduler = self.engine.get_component("scheduler")
        if scheduler and self.auto_consolidation and self.consolidator:
            scheduler.schedule_task(
                "memory_consolidation",
                self.run_consolidation,
                interval_hours=24,  # Daily task
                description="Consolidate old memories"
            )

        if scheduler and self.auto_pruning and self.pruner:
            scheduler.schedule_task(
                "memory_pruning",
                self.run_pruning,
                interval_hours=48,  # Every two days
                description="Prune old and redundant memories"
            )

        self.logger.info("Memory Component initialization complete")

    def add_memory(self, text, memory_type="episodic", metadata=None, importance=None):
        """Add a memory with the appropriate type and importance scoring"""
        if not text or not self.memory_manager:
            return None

        if metadata is None:
            metadata = {}

        # Ensure all metadata values are primitive types
        sanitized_metadata = {}
        for key, value in metadata.items():
            if isinstance(value, (list, dict, tuple, set)):
                sanitized_metadata[key] = str(value)
            else:
                sanitized_metadata[key] = value

        # Score importance if not provided
        if importance is None and self.importance_scorer:
            importance = self.importance_scorer.score_memory_importance(text, sanitized_metadata)

        if importance is not None:
            sanitized_metadata["importance"] = importance

        # Add to the appropriate collection based on type
        if memory_type == "episodic":
            return self.memory_manager.add_episodic_memory(text, sanitized_metadata)
        elif memory_type == "semantic":
            return self.memory_manager.add_semantic_memory(text, sanitized_metadata)
        elif memory_type == "procedural":
            return self.memory_manager.add_procedural_memory(text, sanitized_metadata)
        else:
            self.logger.warning(f"Unknown memory type: {memory_type}, using episodic")
            return self.memory_manager.add_episodic_memory(text, sanitized_metadata)

    def search_memories(self, query, memory_type=None, n_results=5, metadata_filter=None):
        """Search memories with optional type filtering"""
        if not query or not self.memory_manager:
            return []

        if memory_type == "episodic":
            return self.memory_manager.search_episodic_memory(query, n_results)
        elif memory_type == "semantic":
            return self.memory_manager.search_semantic_memory(query, n_results)
        elif memory_type == "procedural":
            return self.memory_manager.search_procedural_memory(query, n_results)
        else:
            return self.memory_manager.search_all_memories(query, n_results)

    def get_memory_by_id(self, memory_id):
        """Get a specific memory by ID"""
        if not memory_id or not self.memory_manager:
            return None

        return self.memory_manager.get_memory_by_id(memory_id)

    def update_memory(self, memory_id, text, metadata=None):
        """Update an existing memory"""
        if not memory_id or not text or not self.memory_manager:
            return False

        return self.memory_manager.update_memory(memory_id, text, metadata)

    def delete_memory(self, memory_id):
        """Delete a memory by ID"""
        if not memory_id or not self.memory_manager:
            return False

        return self.memory_manager.delete_memory(memory_id)

    def create_conversation_thread(self, title=None):
        """Create a new conversation thread"""
        if not self.thread_manager:
            return None

        return self.thread_manager.create_thread(title)

    def get_thread(self, thread_id):
        """Get an active conversation thread"""
        if not thread_id or not self.thread_manager:
            return None

        return self.thread_manager.get_thread(thread_id)

    def load_thread(self, thread_id):
        """Load a conversation thread from memory"""
        if not thread_id or not self.thread_manager:
            return None

        return self.thread_manager.load_thread(thread_id)

    def list_recent_threads(self, limit=10):
        """List recent conversation threads"""
        if not self.thread_manager:
            return []

        return self.thread_manager.list_recent_threads(limit)

    def generate_memory_graph(self, central_query, depth=2, max_connections=20):
        """Generate a graph visualization of memory connections"""
        if not central_query or not self.visualizer:
            return None

        return self.visualizer.generate_memory_graph(central_query, depth, max_connections)

    def visualize_memory_graph(self, graph, filename=None):
        """Visualize a memory graph"""
        if not graph or not self.visualizer:
            return None

        return self.visualizer.visualize_graph(graph, filename)

    def run_consolidation(self):
        """Run the memory consolidation process"""
        if not self.consolidator:
            return "Consolidator not available"

        self.logger.info("Running memory consolidation")
        result = self.consolidator.consolidate_old_memories(days_threshold=self.consolidation_days)
        self.logger.info(f"Consolidation complete: {result}")
        return result

    def run_pruning(self):
        """Run the memory pruning process"""
        if not self.pruner:
            return "Pruner not available"

        self.logger.info("Running memory pruning")

        # Prune old memories
        old_result = self.pruner.prune_old_memories(
            days_threshold=self.pruning_days,
            importance_threshold=self.importance_threshold
        )
        self.logger.info(f"Old memory pruning: {old_result}")

        # Prune duplicates
        dup_result = self.pruner.prune_duplicate_memories()
        self.logger.info(f"Duplicate pruning: {dup_result}")

        return f"{old_result}; {dup_result}"

    def shutdown(self):
        """Shutdown the memory component"""
        self.logger.info("Shutting down Memory Component")
        # Any cleanup needed before shutdown