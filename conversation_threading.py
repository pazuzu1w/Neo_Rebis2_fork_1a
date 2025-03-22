# conversation_threading.py
import uuid
import datetime
import json
import os
from typing import List, Dict, Optional


class ConversationThread:
    def __init__(self, memory_manager, thread_id=None, title=None):
        self.memory_manager = memory_manager
        self.thread_id = thread_id if thread_id else str(uuid.uuid4())
        self.title = title if title else f"Conversation {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"
        self.messages = []
        self.created_at = datetime.datetime.now().isoformat()
        self.updated_at = self.created_at
        self.metadata = {}

    def add_message(self, text, role):
        """Add a message to the thread"""
        if not text:
            return None

        message_id = str(uuid.uuid4())
        timestamp = datetime.datetime.now().isoformat()

        # Create message structure
        message = {
            "id": message_id,
            "thread_id": self.thread_id,
            "text": text,
            "role": role,
            "timestamp": timestamp
        }

        # Add to local cache
        self.messages.append(message)

        # Update thread metadata
        self.updated_at = timestamp

        # Store in memory system for persistence
        if self.memory_manager:
            metadata = {
                "type": "message",
                "role": role,
                "thread_id": self.thread_id,
                "timestamp": timestamp
            }
            self.memory_manager.add_memory(text, metadata, message_id)

        return message_id

    def get_messages(self, limit=None):
        """Get recent messages from thread"""
        if limit:
            return self.messages[-limit:]
        return self.messages

    def get_full_thread(self):
        """Get all messages in the thread"""
        return self.messages

    def format_for_model(self, system_prompt=None, limit=None):
        """Format thread messages for model input"""
        formatted = []

        # Add system prompt if provided
        if system_prompt:
            formatted.append({
                "role": "system",
                "content": system_prompt
            })

        # Add messages, with optional limit
        messages = self.messages
        if limit and len(messages) > limit:
            messages = messages[-limit:]

        for msg in messages:
            # Convert internal role format to model format
            role = "assistant" if msg["role"] == "ai" else msg["role"]
            formatted.append({
                "role": role,
                "content": msg["text"]
            })

        return formatted

    def save_thread_metadata(self):
        """Save thread metadata to memory system"""
        if not self.memory_manager:
            return False

        metadata = {
            "type": "thread_metadata",
            "thread_id": self.thread_id,
            "title": self.title,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "message_count": len(self.messages)
        }

        # Combine with any additional metadata
        metadata.update(self.metadata)

        # Store in memory
        memory_id = f"thread:{self.thread_id}:metadata"
        content = f"Conversation thread: {self.title}"

        self.memory_manager.add_memory(content, metadata, memory_id)
        return True


class ThreadManager:
    def __init__(self, memory_manager):
        self.memory_manager = memory_manager
        self.active_threads = {}  # Cache of active threads

    def create_thread(self, title=None):
        """Create a new conversation thread"""
        thread = ConversationThread(self.memory_manager, title=title)
        self.active_threads[thread.thread_id] = thread

        # Save metadata immediately
        thread.save_thread_metadata()
        return thread

    def get_thread(self, thread_id):
        """Get a thread from cache or load it"""
        if thread_id in self.active_threads:
            return self.active_threads[thread_id]

        # Try to load from memory
        return self.load_thread(thread_id)

    def load_thread(self, thread_id):
        """Load a thread from memory"""
        if not self.memory_manager:
            return None

        # First get thread metadata
        metadata_id = f"thread:{thread_id}:metadata"
        metadata_memory = self.memory_manager.get_memory_by_id(metadata_id)

        if not metadata_memory:
            return None

        # Create thread object
        thread = ConversationThread(
            self.memory_manager,
            thread_id=thread_id,
            title=metadata_memory["metadata"].get("title")
        )

        # Update thread metadata from memory
        thread.created_at = metadata_memory["metadata"].get("created_at", thread.created_at)
        thread.updated_at = metadata_memory["metadata"].get("updated_at", thread.updated_at)

        # Load messages for this thread
        messages = self.memory_manager.search_memory(
            query="",  # Empty query
            n_results=100,  # Reasonable limit
            metadata_filter={"thread_id": {"$eq": thread_id}, "type": {"$eq": "message"}}
        )

        # Sort by timestamp
        messages.sort(key=lambda x: x["metadata"].get("timestamp", ""))

        # Add to thread
        for msg in messages:
            message = {
                "id": msg["id"],
                "thread_id": thread_id,
                "text": msg["text"],
                "role": msg["metadata"].get("role", "user"),
                "timestamp": msg["metadata"].get("timestamp")
            }
            thread.messages.append(message)

        # Cache and return
        self.active_threads[thread_id] = thread
        return thread

    def delete_thread(self, thread_id):
        """Delete a thread and all its messages"""
        if thread_id in self.active_threads:
            del self.active_threads[thread_id]

        # TODO: Implement deletion of all thread messages from memory
        # This would require a search + delete operation on the memory manager

    def list_recent_threads(self, limit=10):
        """List recent conversation threads"""
        if not self.memory_manager:
            return []

        # Search for thread metadata entries
        threads = self.memory_manager.search_memory(
            query="Conversation thread",
            n_results=limit,
            metadata_filter={"type": {"$eq": "thread_metadata"}}
        )

        # Format results
        thread_list = []
        for thread in threads:
            thread_list.append({
                "id": thread["metadata"].get("thread_id"),
                "title": thread["metadata"].get("title"),
                "updated_at": thread["metadata"].get("updated_at"),
                "message_count": thread["metadata"].get("message_count", 0)
            })

        # Sort by updated_at
        thread_list.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
        return thread_list