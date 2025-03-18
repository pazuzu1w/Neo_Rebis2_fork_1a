import chromadb
from typing import List, Dict
import os # We will use it to define the persistance folder


class MemoryManager:
    def __init__(self, persist_directory="neo_rebis_memory"):
        self.persist_directory = persist_directory
        if not os.path.exists(self.persist_directory):
          os.makedirs(self.persist_directory)
        self.client = chromadb.PersistentClient(path=self.persist_directory)
        self.collection = self.client.get_or_create_collection(name="neo_rebis_memory")

    def store_memory(self, content: str, file_path: str, metadata: Dict = None):
        """Stores a chunk of information in the vector database."""

        # Prepare metadata
        if metadata is None:
            metadata = {}
        metadata["file_path"] = file_path
        # Store in the database
        self.collection.add(
            documents=[content],  # Store the original content
            metadatas=[metadata],
            ids=[file_path]  # Use a unique ID (filepath for simplicity)
        )
        return {"status": "ok", "message": f"content from {file_path} was stored"}

    def retrieve_memory(self, query: str, n_results: int = 5) -> List[str]:
        """Retrieves relevant chunks of information based on a query."""

        # Query the database
        results = self.collection.query(
            query_texts=[query], #We use query_text instead of embeddings
            n_results=n_results
        )
        # results is a dict of lists.
        return results['documents'][0]  # We return a list of strings

    def list_memory(self):
      return self.collection.peek()

    def delete_all(self):
      self.client.delete_collection(name="neo_rebis_memory")
      return {"status":"ok", "message":"memory deleted"}