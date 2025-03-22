# conversation_threading.py
import uuid
from datetime import datetime


class ConversationThread:
    def __init__(self, memory_manager, title=None):
        self.memory_manager = memory_manager
        self.thread_id = str(uuid.uuid4())
        self.title = title or f"Conversation {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        self.messages = []
        self.metadata = {
            "created_at": datetime.now().isoformat(),
            "type": "conversation_thread"
        }

    def add_message(self, text, speaker, metadata=None):
        """Add a message to the thread"""
        if metadata is None:
            metadata = {}

        message_id = str(uuid.uuid4())
        timestamp = datetime.datetime.now().isoformat()

        # Prepare message metadata
        message_metadata = {
            "thread_id": self.thread_id,
            "message_id": message_id,
            "timestamp": timestamp,
            "speaker": speaker,
            "position": len(self.messages),
            "type": "message"
        }

        # Add custom metadata, ensuring primitive types
        for key, value in metadata.items():
            if isinstance(value, (list, dict, tuple, set)):
                message_metadata[key] = str(value)
            else:
                message_metadata[key] = value

        # Add to thread's message list
        self.messages.append({
            "id": message_id,
            "text": text,
            "speaker": speaker,
            "timestamp": timestamp
        })

        # Store in memory
        mem_id = self.memory_manager.add_episodic_memory(text, message_metadata)

        return message_id

    def get_thread_summary(self):
        """Get a summary of the conversation thread"""
        if not self.messages:
            return "Empty conversation"

        # Get first, last and count of messages
        first_msg = self.messages[0]
        last_msg = self.messages[-1]
        msg_count = len(self.messages)

        # Calculate duration
        try:
            start_time = datetime.fromisoformat(first_msg["timestamp"])
            end_time = datetime.fromisoformat(last_msg["timestamp"])
            duration = end_time - start_time
            duration_str = f"{duration.total_seconds() / 60:.1f} minutes"
        except:
            duration_str = "unknown duration"

        # Count messages by speaker
        speakers = {}
        for msg in self.messages:
            speakers[msg["speaker"]] = speakers.get(msg["speaker"], 0) + 1

        speaker_str = ", ".join([f"{speaker}: {count}" for speaker, count in speakers.items()])

        return f"{self.title}: {msg_count} messages over {duration_str} ({speaker_str})"

    def get_full_thread(self):
        """Get all messages in the thread"""
        return self.messages

    def save_thread_metadata(self):
        """Save the thread metadata to memory"""
        metadata = {
            "thread_id": self.thread_id,
            "title": self.title,
            "message_count": len(self.messages),
            "speakers": list(set(msg["speaker"] for msg in self.messages)),
            "created_at": self.metadata["created_at"],
            "last_updated": datetime.now().isoformat(),
            "type": "conversation_thread"
        }

        # Create a summary of the thread
        summary = self.get_thread_summary()

        # Store in semantic memory
        self.memory_manager.add_semantic_memory(summary, metadata)


class ThreadManager:
    def __init__(self, memory_manager):
        self.memory_manager = memory_manager
        self.active_threads = {}

    def create_thread(self, title=None):
        """Create a new conversation thread"""
        thread = ConversationThread(self.memory_manager, title)
        self.active_threads[thread.thread_id] = thread
        return thread

    def get_thread(self, thread_id):
        """Get an active thread by ID"""
        return self.active_threads.get(thread_id)

    def load_thread(self, thread_id):
        """Load a thread from memory by ID"""
        # Search for thread metadata
        thread_meta = self.memory_manager.semantic_collection.get(
            where={"thread_id": thread_id, "type": "conversation_thread"}
        )

        if not thread_meta["ids"]:
            return None

        # Create thread object
        thread = ConversationThread(self.memory_manager)
        thread.thread_id = thread_id
        thread.title = thread_meta["metadatas"][0].get("title", "Untitled Thread")
        thread.metadata = thread_meta["metadatas"][0]

        # Load all messages in this thread
        messages = self.memory_manager.episodic_collection.get(
            where={"thread_id": thread_id, "type": "message"}
        )

        if messages["ids"]:
            # Sort by position
            sorted_msgs = sorted(zip(messages["ids"], messages["documents"], messages["metadatas"]),
                                 key=lambda x: x[2].get("position", 0))

            # Add to thread
            for msg_id, text, metadata in sorted_msgs:
                thread.messages.append({
                    "id": msg_id,
                    "text": text,
                    "speaker": metadata.get("speaker", "unknown"),
                    "timestamp": metadata.get("timestamp", "")
                })

        # Add to active threads
        self.active_threads[thread_id] = thread
        return thread

    def list_recent_threads(self, limit=10):
        """List recent conversation threads"""
        threads = self.memory_manager.semantic_collection.get(
            where={"type": "conversation_thread"},
            limit=100  # Get more than needed for sorting
        )

        if not threads["ids"]:
            return []

        # Sort by last_updated
        sorted_threads = sorted(zip(threads["ids"], threads["documents"], threads["metadatas"]),
                                key=lambda x: x[2].get("last_updated", ""), reverse=True)

        # Return only requested number
        return [{
            "id": thread_id,
            "summary": summary,
            "metadata": metadata
        } for thread_id, summary, metadata in sorted_threads[:limit]]