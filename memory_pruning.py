# memory_pruning.py
from datetime import datetime, timedelta


class MemoryPruner:
    def __init__(self, memory_manager, importance_scorer):
        self.memory_manager = memory_manager
        self.importance_scorer = importance_scorer

    def prune_old_memories(self, days_threshold=90, importance_threshold=30):
        """Remove old, unimportant memories"""
        cutoff_date = datetime.now() - timedelta(days=days_threshold)
        cutoff_str = cutoff_date.isoformat()

        # Get old memories from all collections
        collections = [
            self.memory_manager.episodic_collection,
            self.memory_manager.semantic_collection,
            self.memory_manager.procedural_collection
        ]

        pruned_count = 0

        for collection in collections:
            old_memories = collection.get(
                where={"timestamp": {"$lt": cutoff_str}}
            )

            if not old_memories["ids"]:
                continue

            for i, mem_id in enumerate(old_memories["ids"]):
                text = old_memories["documents"][i]
                metadata = old_memories["metadatas"][i]

                # Score importance
                importance = self.importance_scorer.score_memory_importance(text, metadata)

                # If below threshold, prune it
                if importance < importance_threshold:
                    collection.delete(ids=[mem_id])
                    pruned_count += 1

        return f"Pruned {pruned_count} low-importance old memories"

    def prune_duplicate_memories(self, similarity_threshold=0.95):
        """Remove near-duplicate memories"""
        collections = [
            self.memory_manager.episodic_collection,
            self.memory_manager.semantic_collection,
            self.memory_manager.procedural_collection
        ]

        pruned_count = 0

        for collection in collections:
            # Get all memories
            all_memories = collection.get()

            if not all_memories["ids"]:
                continue

            # Check each memory against others
            for i, mem_id in enumerate(all_memories["ids"]):
                text = all_memories["documents"][i]

                # Skip if already processed
                if text is None:
                    continue

                # Search for similar memories
                similar = collection.query(
                    query_texts=[text],
                    n_results=10
                )

                # First result is always the same document
                for j, sim_id in enumerate(similar["ids"][0][1:], 1):  # Skip first (self)
                    # If similarity above threshold
                    if similar["distances"][0][j] < (1.0 - similarity_threshold):
                        # Keep the newer one
                        idx = all_memories["ids"].index(sim_id)
                        timestamp1 = all_memories["metadatas"][i].get("timestamp", "")
                        timestamp2 = all_memories["metadatas"][idx].get("timestamp", "")

                        # If second memory is newer, delete first
                        if timestamp2 > timestamp1:
                            collection.delete(ids=[mem_id])
                        else:
                            collection.delete(ids=[sim_id])
                            # Mark as processed to avoid double deletion
                            all_memories["documents"][idx] = None

                        pruned_count += 1
                        break

        return f"Pruned {pruned_count} duplicate memories"