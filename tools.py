import os
from tavily import TavilyClient
from dotenv import load_dotenv
from typing import Dict
from memory import MemoryManager  # Import the MemoryManager

load_dotenv()

tavily_api_key = os.getenv("TAVILY_API_KEY")
tavily = TavilyClient(api_key=tavily_api_key)

# Initialize the MemoryManager.  This should ideally be done *once*
# at the application level (e.g., in main.py) and passed to wherever
# it's needed.  But for now, we'll do it here.
memory_manager = MemoryManager()

def create_folder(path: str):
    """Creates a new folder at the specified path."""
    try:
        os.makedirs(path, exist_ok=True)
        return f"Folder created: {path}"
    except Exception as e:
        return f"Error creating folder: {str(e)}"

def create_file(path: str, content: str = ""):
    """Creates a new file at the specified path with optional content."""
    try:
        with open(path, "w") as f: f.write(content)
        return f"File created: {path}"
    except Exception as e:
        return f"Error creating file: {str(e)}"

def write_to_file(path: str, content: str):
    """Writes content to an existing file at the specified path."""
    try:
        with open(path, "w") as f: f.write(content)
        return f"Content written to file: {path}"
    except Exception as e:
        return f"Error writing to file: {str(e)}"

def read_file(file_path: str):
    """Reads any file on the disk. Args: file_path (str):
    The full path to the file. """
    if os.path.exists(file_path):
        with open(file_path, "r") as file:
            print(f"Reading file '{file_path}'")
            return file.read()
    else:
        print(f"File '{file_path}' not found.")
        return f"File '{file_path}' not found."

def list_files(path: str = "."):
    """Lists all files and directories in the specified path
    (default: current directory)."""
    try:
        files = os.listdir(path)
        return "\n".join(files)
    except Exception as e:
        return f"Error listing files: {str(e)}"

def tavily_search(query: str):
    """Performs a web search using the Tavily API."""
    try:
        response = tavily.qna_search(query=query, search_depth="advanced")
        print(f"Search results for '{query}': {response}")
        return response
    except Exception as e:
        return f"Error performing search: {str(e)}"

# --- Memory Management Functions ---

def store_memory(content: str, file_path: str, metadata: Dict = {1}) -> dict:
    """Stores a chunk of information in the vector database."""
    # Delegate to the MemoryManager instance
    return memory_manager.store_memory(content, file_path, metadata)

def retrieve_memory(query: str, n_results: int = 5) -> dict:
    """Retrieves relevant chunks of information based on a query."""
    # Delegate to the MemoryManager instance
    retrieved_data = memory_manager.retrieve_memory(query, n_results)
    # Wrap as a dict
    return {"result": retrieved_data} # Wrap the result

def list_memory() -> dict:
    """Retrieves all memory data based on a query."""
    # Delegate to the MemoryManager instance
    all_data = memory_manager.list_memory()
    # Wrap as a dict
    return {"result": all_data} # Wrap the result

def delete_all_memories()-> dict:
    return memory_manager.delete_all()