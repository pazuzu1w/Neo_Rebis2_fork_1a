import chromadb
from chromadb.utils import embedding_functions
import uuid
from typing import List, Dict, Optional, Tuple
import os
import datetime
import json
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from collections import Counter
import re


class TopicExtractor:
    def __init__(self):
        # Download required NLTK data (only needed once)
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt')
        try:
            nltk.data.find('corpora/stopwords')
        except LookupError:
            nltk.download('stopwords')
        try:
            nltk.data.find('corpora/wordnet')
        except LookupError:
            nltk.download('wordnet')

        self.stop_words = set(stopwords.words('english'))
        self.lemmatizer = WordNetLemmatizer()

        # Add magical/esoteric terminology to our processing
        self.magical_terms = {
            'chaos', 'magic', 'sigil', 'ritual', 'symbol', 'trance',
            'synchronicity', 'invocation', 'evocation', 'banishing',
            'gnosis', 'servitor', 'egregore', 'thoughtform', 'divination'
        }

    def extract_topics(self, text, top_n=5):
        """Extract the main topics from a text."""
        if not text:
            return []

        # Preprocess the text
        # Convert to lowercase and remove punctuation
        text = re.sub(r'[^\w\s]', '', text.lower())

        # Tokenize
        tokens = word_tokenize(text)

        # Remove stopwords and short words, but keep magical terms
        filtered_tokens = [
            self.lemmatizer.lemmatize(word) for word in tokens
            if (word not in self.stop_words and len(word) > 3) or word in self.magical_terms
        ]

        # Count word frequency
        word_freq = Counter(filtered_tokens)

        # Return top N topics
        return word_freq.most_common(top_n)


class MemoryManager:
    def __init__(self,
                 persist_directory: str = "./chroma_db",
                 collection_name: str = "memory_collection"):
        """Initialize the memory system with ChromaDB."""
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

        # Create topic extractor
        self.topic_extractor = TopicExtractor()

        # Create collections for different memory types
        self.episodic_collection = self._get_or_create_collection("episodic_memory")
        self.semantic_collection = self._get_or_create_collection("semantic_memory")
        self.procedural_collection = self._get_or_create_collection("procedural_memory")

    def add_memory(self,
                   text: str,
                   metadata: Dict = None,
                   id: str = None) -> str:
        """Add a memory to the database."""
        if not text:
            return None

        # Generate a unique ID if not provided
        memory_id = id if id else str(uuid.uuid4())

        # Create default metadata if not provided
        if metadata is None:
            metadata = {}

        # Convert any non-primitive types to strings to satisfy ChromaDB requirements
        sanitized_metadata = {}
        for key, value in metadata.items():
            if isinstance(value, (list, dict, tuple, set)):
                sanitized_metadata[key] = str(value)
            else:
                sanitized_metadata[key] = value

        # Add timestamp if not in metadata
        if "timestamp" not in sanitized_metadata:
            sanitized_metadata["timestamp"] = datetime.datetime.now().isoformat()

        # Add memory to collection
        self.collection.add(
            documents=[text],
            metadatas=[sanitized_metadata],
            ids=[memory_id]
        )

        return memory_id
    def search_by_topic(self, topic, n_results=5):
        """Search for memories containing a specific topic."""
        # Build filters for each possible topic field
        filters = []
        for i in range(10):  # Assuming we store up to 10 topics
            filter_key = f"topic_{i}"
            filters.append({filter_key: topic})

        # Execute search with proper OR condition format
        results = self.collection.query(
            query_texts=["topic search"],  # Just a placeholder
            n_results=n_results,
            where={"$or": filters} if filters else None
        )

        # Format results
        memories = []
        if results["documents"] and len(results["documents"]) > 0:
            for i, doc in enumerate(results["documents"][0]):
                memories.append({
                    "id": results["ids"][0][i],
                    "text": doc,
                    "metadata": results["metadatas"][0][i],
                })

        return memories

    def search_memory(self, query: str, n_results: int = 5, metadata_filter: Dict = None) -> List[Dict]:
        """Search for memories similar to the query."""
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
        """Retrieve a specific memory by its ID."""
        results = self.collection.get(ids=[memory_id])

        if results["documents"] and len(results["documents"]) > 0:
            return {
                "id": memory_id,
                "text": results["documents"][0],
                "metadata": results["metadatas"][0] if results["metadatas"] else {}
            }
        return None

    def update_memory(self, memory_id: str, text: str, metadata: Dict = None) -> bool:
        """Update an existing memory."""
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
        """Delete a memory by its ID."""
        try:
            self.collection.delete(ids=[memory_id])
            return True
        except Exception as e:
            print(f"Error deleting memory: {e}")
            return False

    def add_conversation(self, user_message: str, ai_response: str) -> Tuple[str, str]:
        """Store a conversation exchange between user and AI."""
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
        """Get recent conversation history."""
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

    def _get_or_create_collection(self, collection_name):
        """Get or create a ChromaDB collection"""
        try:
            collection = self.client.get_collection(
                name=collection_name,
                embedding_function=self.embedding_function
            )
        except:
            collection = self.client.create_collection(
                name=collection_name,
                embedding_function=self.embedding_function
            )
        return collection

    def add_episodic_memory(self, text, metadata=None):
        """Add a memory of a specific event or conversation"""
        if metadata is None:
            metadata = {}
        metadata["memory_type"] = "episodic"
        return self._add_to_collection(self.episodic_collection, text, metadata)

    def add_semantic_memory(self, text, metadata=None):
        """Add factual knowledge to semantic memory"""
        if metadata is None:
            metadata = {}
        metadata["memory_type"] = "semantic"
        return self._add_to_collection(self.semantic_collection, text, metadata)

    def add_procedural_memory(self, text, metadata=None):
        """Add procedural knowledge (how to do things)"""
        if metadata is None:
            metadata = {}
        metadata["memory_type"] = "procedural"
        return self._add_to_collection(self.procedural_collection, text, metadata)

    def _add_to_collection(self, collection, text, metadata=None):
        """Internal method to add to a specific collection"""
        memory_id = str(uuid.uuid4())

        if metadata is None:
            metadata = {}

        # Ensure all metadata values are primitive types
        for key, value in list(metadata.items()):  # Use list() to avoid modifying during iteration
            if isinstance(value, (list, dict, tuple)):
                metadata[key] = str(value)

        if "timestamp" not in metadata:
            metadata["timestamp"] = datetime.datetime.now().isoformat()

        collection.add(
            documents=[text],
            metadatas=[metadata],
            ids=[memory_id]
        )

        return memory_id

    def search_all_memories(self, query, n_results=5):
        """Search across all memory types"""
        episodic = self.search_episodic_memory(query, n_results)
        semantic = self.search_semantic_memory(query, n_results)
        procedural = self.search_procedural_memory(query, n_results)

        # Combine and sort by relevance (distance)
        all_memories = episodic + semantic + procedural
        all_memories.sort(key=lambda x: x.get("distance", float("inf")))

        return all_memories[:n_results]

    def search_episodic_memory(self, query, n_results=5):
        """Search only episodic memories"""
        return self._search_collection(self.episodic_collection, query, n_results)

    def search_semantic_memory(self, query, n_results=5):
        """Search only semantic memories"""
        return self._search_collection(self.semantic_collection, query, n_results)

    def search_procedural_memory(self, query, n_results=5):
        """Search only procedural memories"""
        return self._search_collection(self.procedural_collection, query, n_results)

    def _search_collection(self, collection, query, n_results=5):
        """Internal method to search a specific collection"""
        if not query:
            return []

        results = collection.query(
            query_texts=[query],
            n_results=n_results
        )

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


# Create a singleton instance of the memory manager
memory_manager = MemoryManager()