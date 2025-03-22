# memory_consolidation.py
from datetime import datetime, timedelta


class MemoryConsolidator:
    def __init__(self, memory_manager, model_interface):
        self.memory_manager = memory_manager
        self.model_interface = model_interface  # This would be your AI model interface

    def consolidate_old_memories(self, days_threshold=30, batch_size=10):
        """Consolidate memories older than threshold days"""
        cutoff_date = datetime.now() - timedelta(days=days_threshold)
        cutoff_str = cutoff_date.isoformat()

        # Get old episodic memories
        old_memories = self.memory_manager.episodic_collection.get(
            where={"timestamp": {"$lt": cutoff_str}}
        )

        if not old_memories["ids"]:
            return "No old memories to consolidate"

        # Process in batches
        for i in range(0, len(old_memories["ids"]), batch_size):
            batch_ids = old_memories["ids"][i:i + batch_size]
            batch_docs = old_memories["documents"][i:i + batch_size]
            batch_metadatas = old_memories["metadatas"][i:i + batch_size]

            # Create a summary of this batch
            combined_text = "\n\n".join(batch_docs)
            summary_prompt = f"Please summarize these memories concisely, preserving key information:\n\n{combined_text}"

            summary = self.model_interface.generate_text(summary_prompt)

            # Create a consolidated memory
            consolidated_metadata = {
                "memory_type": "consolidated_episodic",
                "timestamp": datetime.now().isoformat(),
                "source_ids": batch_ids,
                "source_count": len(batch_ids),
                "oldest_source": min(meta.get("timestamp", cutoff_str) for meta in batch_metadatas),
                "newest_source": max(meta.get("timestamp", cutoff_str) for meta in batch_metadatas)
            }

            # Store the consolidated memory
            self.memory_manager.add_semantic_memory(summary, consolidated_metadata)

            # Optionally, remove or archive the old memories
            for mem_id in batch_ids:
                self.memory_manager.episodic_collection.delete(ids=[mem_id])

        return f"Consolidated {len(old_memories['ids'])} old memories"