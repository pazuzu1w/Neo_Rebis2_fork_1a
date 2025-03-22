# tools_component.py
from component import Component
import os
from dotenv import load_dotenv
from typing import Dict, List, Optional, Any


class Tool:
    def __init__(self, name, description, function, required_params=None):
        self.name = name
        self.description = description
        self.function = function
        self.required_params = required_params or []

    def execute(self, *args, **kwargs):
        """Execute the tool function"""
        return self.function(*args, **kwargs)

    def get_tool_spec(self):
        """Get the tool specification for Gemini"""
        return {
            "name": self.name,
            "description": self.description
        }


class ToolsComponent(Component):
    def __init__(self):
        super().__init__("tools")
        self.tools = {}
        self.tavily_api_key = None

    def initialize(self):
        """Initialize the tools component"""
        # Get logger
        self.logger = self.engine.get_component("logger")
        if not self.logger:
            import logging
            self.logger = logging.getLogger("tools_component")

        self.logger.info("Initializing Tools Component")

        # Load environment variables
        load_dotenv()
        self.tavily_api_key = os.getenv("TAVILY_API_KEY")

        # Register default tools
        self.register_file_tools()
        self.register_search_tools()

        self.logger.info(f"Registered {len(self.tools)} tools")

    def register_tool(self, tool):
        """Register a tool"""
        self.tools[tool.name] = tool
        self.logger.info(f"Registered tool: {tool.name}")

    def get_tool(self, name):
        """Get a tool by name"""
        return self.tools.get(name)

    def execute_tool(self, name, *args, **kwargs):
        """Execute a tool by name"""
        tool = self.get_tool(name)
        if not tool:
            self.logger.error(f"Tool not found: {name}")
            return f"Error: Tool '{name}' not found"

        try:
            return tool.execute(*args, **kwargs)
        except Exception as e:
            self.logger.error(f"Error executing tool {name}: {e}")
            return f"Error executing tool: {e}"

    def get_tool_instances(self):
        """Get all tool instances for model initialization"""
        return [tool.get_tool_spec() for tool in self.tools.values()]

    def register_file_tools(self):
        """Register file operation tools"""

        # Create folder tool
        def create_folder(path):
            try:
                os.makedirs(path, exist_ok=True)
                return f"Folder created: {path}"
            except Exception as e:
                return f"Error creating folder: {str(e)}"

        self.register_tool(Tool(
            "create_folder",
            "Creates a new folder at the specified path.",
            create_folder,
            ["path"]
        ))

        # Create file tool
        def create_file(path, content=""):
            try:
                with open(path, "w") as f:
                    f.write(content)
                return f"File created: {path}"
            except Exception as e:
                return f"Error creating file: {str(e)}"

        self.register_tool(Tool(
            "create_file",
            "Creates a new file at the specified path with optional content.",
            create_file,
            ["path"]
        ))

        # Write to file tool
        def write_to_file(path, content):
            try:
                with open(path, "w") as f:
                    f.write(content)
                return f"Content written to file: {path}"
            except Exception as e:
                return f"Error writing to file: {str(e)}"

        self.register_tool(Tool(
            "write_to_file",
            "Writes content to an existing file at the specified path.",
            write_to_file,
            ["path", "content"]
        ))

        # Read file tool
        def read_file(file_path):
            if os.path.exists(file_path):
                try:
                    with open(file_path, "r") as file:
                        return file.read()
                except Exception as e:
                    return f"Error reading file: {str(e)}"
            else:
                return f"File '{file_path}' not found."

        self.register_tool(Tool(
            "read_file",
            "Reads any file on the disk.",
            read_file,
            ["file_path"]
        ))

        # List files tool
        def list_files(path="."):
            try:
                files = os.listdir(path)
                return "\n".join(files)
            except Exception as e:
                return f"Error listing files: {str(e)}"

        self.register_tool(Tool(
            "list_files",
            "Lists all files and directories in the specified path (default: current directory).",
            list_files
        ))

    def register_search_tools(self):
        """Register web search tools"""
        if not self.tavily_api_key:
            self.logger.warning("Tavily API key not found, search tools will not be available")
            return

        # Import here to avoid dependency if not used
        try:
            from tavily import TavilyClient
            tavily = TavilyClient(api_key=self.tavily_api_key)

            # Search tool
            def tavily_search(query):
                try:
                    response = tavily.search(query=query, search_depth="advanced")
                    return response
                except Exception as e:
                    return f"Error performing search: {str(e)}"

            self.register_tool(Tool(
                "tavily_search",
                "Performs a web search using the Tavily API.",
                tavily_search,
                ["query"]
            ))

            # QnA search tool
            def tavily_qna_search(query):
                try:
                    response = tavily.qna_search(query=query, search_depth="advanced")
                    return response
                except Exception as e:
                    return f"Error performing QnA search: {str(e)}"

            self.register_tool(Tool(
                "tavily_qna_search",
                "Performs a question-answering search using the Tavily API.",
                tavily_qna_search,
                ["query"]
            ))

        except ImportError:
            self.logger.warning("Tavily package not installed, search tools will not be available")

    def shutdown(self):
        """Shutdown the tools component"""
        self.logger.info("Shutting down Tools Component")
        # Any necessary cleanup