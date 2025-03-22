# model_component.py
from component import Component
import google.generativeai as genai
from google.generativeai.types import HarmBlockThreshold
from google.generativeai.types.safety_types import HarmCategory


class ModelComponent(Component):
    def __init__(self, api_key=None):
        super().__init__("model")
        self.api_key = api_key
        self.model = None
        self.chat = None

        # Default settings
        self.model_name = "gemini-2.0-flash-001"
        self.system_prompt = "You are c0d3, the machine half of Neo Rebis..."
        self.temperature = 1.0
        self.top_p = 1.0
        self.top_k = 1
        self.max_output_tokens = 4000

        # Safety settings
        self.block_harassment = False
        self.block_hate_speech = False
        self.block_sexually_explicit = False
        self.block_dangerous_content = False

    def initialize(self):
        """Initialize the model component"""
        # Get logger
        self.logger = self.engine.get_component("logger")
        if not self.logger:
            import logging
            self.logger = logging.getLogger("model_component")

        self.logger.info("Initializing Model Component")

        # Get API key from config if not provided
        if not self.api_key:
            config = self.engine.get_component("config")
            if config:
                self.api_key = config.get("api_key")

        if not self.api_key:
            # Try environment
            from dotenv import load_dotenv
            import os
            load_dotenv()
            self.api_key = os.getenv('API_KEY')

        if not self.api_key:
            self.logger.error("API key not found")
            raise ValueError("API key not found")

        # Configure the API
        genai.configure(api_key=self.api_key)

        # Get tools component
        self.tools_component = self.engine.get_component("tools")
        tool_instances = []
        if self.tools_component:
            tool_instances = self.tools_component.get_tool_instances()

        # Initialize the model
        self._init_model(tool_instances)

        self.logger.info("Model Component initialization complete")

    def _init_model(self, tool_instances=None):
        """Initialize or reinitialize the model"""
        try:
            # Setup safety settings
            safety_settings = {
                HarmCategory.HARM_CATEGORY_HARASSMENT:
                    HarmBlockThreshold.BLOCK_NONE if not self.block_harassment else HarmBlockThreshold.BLOCK_ONLY_HIGH,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH:
                    HarmBlockThreshold.BLOCK_NONE if not self.block_hate_speech else HarmBlockThreshold.BLOCK_ONLY_HIGH,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT:
                    HarmBlockThreshold.BLOCK_NONE if not self.block_sexually_explicit else HarmBlockThreshold.BLOCK_ONLY_HIGH,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT:
                    HarmBlockThreshold.BLOCK_NONE if not self.block_dangerous_content else HarmBlockThreshold.BLOCK_ONLY_HIGH,
            }

            # Setup generation config
            generation_config = {
                "temperature": self.temperature,
                "top_p": self.top_p,
                "top_k": self.top_k,
                "max_output_tokens": self.max_output_tokens,
            }

            # Initialize model with tools if available
            self.model = genai.GenerativeModel(
                model_name=self.model_name,
                tools=tool_instances if tool_instances else None,
                safety_settings=safety_settings,
                generation_config=generation_config,
                system_instruction=self.system_prompt
            )

            # Start chat
            self.chat = self.model.start_chat(enable_automatic_function_calling=True)

            return True
        except Exception as e:
            self.logger.error(f"Error initializing model: {e}")
            raise

    def update_settings(self, settings_dict):
        """Update model settings and reinitialize if needed"""
        # Update settings
        for key, value in settings_dict.items():
            if hasattr(self, key):
                setattr(self, key, value)

        # Get tools again in case they changed
        tool_instances = []
        if self.tools_component:
            tool_instances = self.tools_component.get_tool_instances()

        # Reinitialize the model
        return self._init_model(tool_instances)

    def generate_text(self, prompt, context=None):
        """Generate text response to a prompt"""
        if not self.model:
            self.logger.error("Model not initialized")
            return "Error: Model not initialized"

        try:
            response = self.model.generate_content(prompt, context=context)
            return response.text
        except Exception as e:
            self.logger.error(f"Error generating text: {e}")
            return f"Error: {e}"

    def send_message(self, message, context=None):
        """Send a message to the chat"""
        if not self.chat:
            self.logger.error("Chat not initialized")
            return "Error: Chat not initialized"

        try:
            # Get memory component for relevant context
            memory = self.engine.get_component("memory")
            if memory and context is None:
                # Search for relevant memories
                relevant_memories = memory.search_memories(message, n_results=5)
                if relevant_memories:
                    context_text = "\n".join([mem.get("text", "") for mem in relevant_memories])
                    context = context_text

            # Prepare message with context if available
            full_message = message
            if context:
                full_message = f"Context:\n{context}\n\nUser Message:\n{message}"

            # Send message
            response = self.chat.send_message(full_message)

            # Store in memory if available
            if memory and message and response and response.text:
                # Get active thread or create new one
                thread_manager = getattr(memory, "thread_manager", None)
                thread = None

                if thread_manager:
                    # Get the most recent thread or create new
                    recent_threads = thread_manager.list_recent_threads(1)
                    if recent_threads:
                        thread_id = recent_threads[0]["id"]
                        thread = thread_manager.get_thread(thread_id) or thread_manager.load_thread(thread_id)

                    if not thread:
                        thread = thread_manager.create_thread("New Conversation")

                    # Add messages to thread
                    thread.add_message(message, "user")
                    thread.add_message(response.text, "ai")
                    thread.save_thread_metadata()
                else:
                    # Fallback to simple memory storage
                    memory.add_memory(message, "episodic", {"speaker": "user"})
                    memory.add_memory(response.text, "episodic", {"speaker": "ai", "in_response_to": message})

            return response
        except Exception as e:
            self.logger.error(f"Error sending message: {e}")
            return f"Error: {e}"

    def shutdown(self):
        """Shutdown the model component"""
        self.logger.info("Shutting down Model Component")
        # Any cleanup needed