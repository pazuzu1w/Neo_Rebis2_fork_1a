import chromadb
from chromadb.utils import embedding_functions
import uuid
from typing import List, Dict, Optional, Tuple
import os
import datetime
import json


class MemoryManager:
    def __init__(self,
                 persist_directory: str = "./chroma_db",
                 collection_name: str = "memory_collection"):
        """Initialize the memory system with ChromaDB.

        Args:
            persist_directory: Directory to store the ChromaDB data
            collection_name: Name of the collection in ChromaDB
        """
        # Create directory if it doesn't exist
        os.makedirs(persist_directory, exist_ok=True)

        # Initialize the embedding function using SentenceTransformer
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )

        # Initialize ChromaDB client with persistence
        self.client = chromadb.PersistentClient(path=persist_directory)

        # Get or create collection
        try:
            self.collection = self.client.get_collection(
                name=collection_name,
                embedding_function=self.embedding_function
            )
            print(f"Loaded existing collection: {collection_name}")
        except:
            self.collection = self.client.create_collection(
                name=collection_name,
                embedding_function=self.embedding_function
            )
            print(f"Created new collection: {collection_name}")

    def add_memory(self,
                   text: str,
                   metadata: Dict = None,
                   id: str = None) -> str:
        """Add a memory to the database.

        Args:
            text: The text content to store
            metadata: Additional metadata about the memory
            id: Optional ID for the memory (generated if not provided)

        Returns:
            The ID of the stored memory
        """
        if not text:
            return None

        # Generate a unique ID if not provided
        memory_id = id if id else str(uuid.uuid4())

        # Create default metadata if not provided
        if metadata is None:
            metadata = {}

        # Add timestamp if not in metadata
        if "timestamp" not in metadata:
            metadata["timestamp"] = datetime.datetime.now().isoformat()

        # Add memory to collection
        self.collection.add(
            documents=[text],
            metadatas=[metadata],
            ids=[memory_id]
        )

        return memory_id

    def search_memory(self,
                      query: str,
                      n_results: int = 5,
                      metadata_filter: Dict = None) -> List[Dict]:
        """Search for memories similar to the query.

        Args:
            query: The search query
            n_results: Maximum number of results to return
            metadata_filter: Optional filter for metadata

        Returns:
            List of memory items with text, metadata and similarity score
        """
        if not query:
            return []

        # Execute search
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            where=metadata_filter
        )

        # Format results for ease of use
        memories = []
        if results["documents"] and len(results["documents"]) > 0:
            for i, doc in enumerate(results["documents"][0]):
                memories.append({
                    "id": results["ids"][0][i],
                    "text": doc,
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i] if "distances" in results else None
                })

        return memories

    def get_memory_by_id(self, memory_id: str) -> Optional[Dict]:
        """Retrieve a specific memory by its ID.

        Args:
            memory_id: The ID of the memory to retrieve

        Returns:
            The memory item or None if not found
        """
        results = self.collection.get(ids=[memory_id])

        if results["documents"] and len(results["documents"]) > 0:
            return {
                "id": memory_id,
                "text": results["documents"][0],
                "metadata": results["metadatas"][0] if results["metadatas"] else {}
            }
        return None

    def update_memory(self, memory_id: str, text: str, metadata: Dict = None) -> bool:
        """Update an existing memory.

        Args:
            memory_id: The ID of the memory to update
            text: The new text content
            metadata: The new metadata (if None, keeps existing metadata)

        Returns:
            True if update was successful, False otherwise
        """
        try:
            # If no new metadata provided, get the existing metadata
            if metadata is None:
                existing = self.get_memory_by_id(memory_id)
                if existing:
                    metadata = existing["metadata"]
                else:
                    metadata = {}

            # Update memory
            self.collection.update(
                ids=[memory_id],
                documents=[text],
                metadatas=[metadata]
            )
            return True
        except Exception as e:
            print(f"Error updating memory: {e}")
            return False

    def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory by its ID.

        Args:
            memory_id: The ID of the memory to delete

        Returns:
            True if deletion was successful
        """
        try:
            self.collection.delete(ids=[memory_id])
            return True
        except Exception as e:
            print(f"Error deleting memory: {e}")
            return False

    def add_conversation(self, user_message: str, ai_response: str) -> Tuple[str, str]:
        """Store a conversation exchange between user and AI.

        Args:
            user_message: The user's message
            ai_response: The AI's response

        Returns:
            Tuple of (user_memory_id, ai_memory_id)
        """
        # Generate a conversation ID to link messages
        conversation_id = str(uuid.uuid4())
        timestamp = datetime.datetime.now().isoformat()

        # Store user message
        user_metadata = {
            "type": "user_message",
            "timestamp": timestamp,
            "conversation_id": conversation_id
        }
        user_id = self.add_memory(user_message, user_metadata)

        # Store AI response
        ai_metadata = {
            "type": "ai_response",
            "timestamp": timestamp,
            "conversation_id": conversation_id,
            "in_response_to": user_id
        }
        ai_id = self.add_memory(ai_response, ai_metadata)

        return (user_id, ai_id)

    def get_conversation_history(self, limit: int = 10) -> List[Dict]:
        """Get recent conversation history.

        Args:
            limit: Maximum number of conversation turns to retrieve

        Returns:
            List of conversation turns, each containing user message and AI response
        """
        # Query for recent AI responses (which link to user messages)
        results = self.collection.query(
            query_texts=["conversation"],  # Generic query to get conversations
            n_results=limit,
            where={"type": "ai_response"}
        )

        conversation_history = []
        if results["documents"] and len(results["documents"]) > 0:
            for i, doc in enumerate(results["documents"][0]):
                metadata = results["metadatas"][0][i]

                # Get the corresponding user message
                user_message = None
                if "in_response_to" in metadata:
                    user_result = self.get_memory_by_id(metadata["in_response_to"])
                    if user_result:
                        user_message = user_result["text"]

                conversation_history.append({
                    "timestamp": metadata.get("timestamp", ""),
                    "conversation_id": metadata.get("conversation_id", ""),
                    "user_message": user_message,
                    "ai_response": doc
                })

        return conversation_history