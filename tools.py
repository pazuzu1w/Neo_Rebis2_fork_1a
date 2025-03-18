import os
from tavily import TavilyClient
from dotenv import load_dotenv

load_dotenv()

tavily_api_key = os.getenv("TAVILY_API_KEY")
tavily = TavilyClient(api_key=tavily_api_key)

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