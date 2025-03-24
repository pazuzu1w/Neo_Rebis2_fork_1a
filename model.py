# model.py - Corrected and significantly improved
import logging

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
        self.model_name = "gemini-1.5-pro-002"  # Use a more reliable default model
        self.system_prompt = "You are c0d3, the machine half of Neo Rebis..."
        self.temperature = 0.7  # More reasonable default temperature
        self.top_p = 0.9
        self.top_k = 40  # Standard top_k value
        self.max_output_tokens = 2048  # Limit output to avoid excessive length

        # Safety settings
        self.block_harassment = True  # Block by default for safety
        self.block_hate_speech = True
        self.block_sexually_explicit = True
        self.block_dangerous_content = True

    def initialize(self):
        """Initialize the model component"""
        self.logger = self.engine.get_component("logger") or logging.getLogger("model_component")
        self.logger.info("Initializing Model Component")

        if not self.api_key:
            config = self.engine.get_component("config")
            if config:
                self.api_key = config.get("api_key")
            if not self.api_key:
                from dotenv import load_dotenv
                import os
                load_dotenv()
                self.api_key = os.getenv('API_KEY')

        if not self.api_key:
            self.logger.error("API key not found")
            raise ValueError("API key not found")

        genai.configure(api_key=self.api_key)
        self.tools_component = self.engine.get_component("tools")
        self._init_model()
        self.logger.info("Model Component initialization complete")

    def _init_model(self, tool_instances=None):
        """Initialize or reinitialize the model."""
        try:
            safety_settings = {
                category: HarmBlockThreshold.BLOCK_ONLY_HIGH
                for category in [
                    HarmCategory.HARM_CATEGORY_HARASSMENT,
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                ]
            }

            generation_config = genai.GenerationConfig(
                temperature=self.temperature,
                top_p=self.top_p,
                top_k=self.top_k,
                max_output_tokens=self.max_output_tokens,
            )

            tools_list = []
            if self.tools_component:
                tools_list = self.tools_component.get_tool_instances()


            self.model = genai.GenerativeModel(
                model_name=self.model_name,
                tools=tools_list,
                safety_settings=safety_settings,
                generation_config=generation_config,
            )
            self.chat = self.model.start_chat()  # No need for automatic function calling here
            return True

        except Exception as e:
            self.logger.error(f"Error initializing model: {e}")
            raise

    def update_settings(self, settings_dict):
        """Update model settings and reinitialize."""
        for key, value in settings_dict.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self._init_model()

    def generate_text(self, prompt, context=None):
        """Generate text (not used directly for chat, but useful for other tasks)."""
        if not self.model:
            return "Error: Model not initialized"
        try:
            response = self.model.generate_content(prompt, context=context)
            return response.text
        except Exception as e:
            self.logger.error(f"Error generating text: {e}")
            return f"Error: {e}"


    def send_message(self, message, context=None):
        """Send a message to the chat and handle the response."""
        if not self.chat:
            self.logger.error("Chat not initialized")
            return "Error: Chat not initialized"

        try:
            # Construct the full prompt (including context, if any)
            full_prompt = []
            if context:
                full_prompt.append(context)  # Add context as a separate part
            full_prompt.append(message)

            # Use the chat object to send the message
            response = self.chat.send_message(full_prompt)

            # Log the response for debugging
            self.logger.debug(f"Raw Gemini response: {response}")


            # Extract and return the text.  Handle potential errors.
            if response and response.text:
                return_text = response.text
            elif response and response.candidates:
                #If there isn't any text check the other responses
                for candidate in response.candidates:
                    if candidate.content and candidate.content.parts:
                        return_text = candidate.content.parts[0].text
                        break
                else: #If there still isn't any text send a default response
                    return_text = "[No response received]"
            else: #If there is no response send a default one
                return_text = "[No response received]"

            # Store in memory if available
            memory = self.engine.get_component("memory")
            if memory:
                thread_manager = getattr(memory, "thread_manager", None)
                if thread_manager:
                    thread = self.get_or_create_thread(thread_manager)
                    thread.add_message(message, "user")
                    thread.add_message(return_text, "ai")
                    thread.save_thread_metadata()  # Save after *each* message
                else:
                    memory.add_memory(message, "episodic", {"speaker": "user"})
                    memory.add_memory(return_text, "episodic", {"speaker": "ai"})
            return return_text

        except Exception as e:
            self.logger.error(f"Error sending message: {e}")
            return f"Error: {e}"

    def get_or_create_thread(self, thread_manager):
        """Helper function to get the current thread or create a new one"""
        recent_threads = thread_manager.list_recent_threads(1)
        if recent_threads:
            thread_id = recent_threads[0]["id"]
            thread = thread_manager.get_thread(thread_id) or thread_manager.load_thread(thread_id)
        else:
            thread = thread_manager.create_thread("New Conversation")
        return thread


    def shutdown(self):
        """Shutdown the model component."""
        self.logger.info("Shutting down Model Component")
        # No specific cleanup needed for the Gemini API