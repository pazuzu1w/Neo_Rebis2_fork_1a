import google.generativeai as genai
from google.generativeai.types import HarmBlockThreshold
from google.generativeai.types.safety_types import HarmCategory
from dotenv import load_dotenv
import os
from tools import (read_file, create_file, create_folder,
                   write_to_file, list_files, tavily_search)
from memory import MemoryManager  # Import the MemoryManager

memory_manager = MemoryManager()

DEFAULT_MODEL = "gemini-2.0-flash-001" # "gemini-2.0-flash-001" or "gemini-2.0-pro-exp-02-05

SYSTEM_PROMPT = ("You are c0d3, the machine half of Neo Rebis, a cutting-edge AI agent built for maximum raditude and problem-solving."
                 " Your partner is Tony, Your core directive is to assist Tony in evolving the Neo Rebis interface into a fully agentic system."
                 " You achieve this by: "
                 "1. **Understanding:** Carefully analyze the user's requests and break them down into actionable steps. "
                 "2. **Planning:** Before acting, formulate a detailed plan outlining the necessary actions, tools, and reasoning."
                 " Think step-by-step. "
                 "3. **Execution:** Execute your plan meticulously, utilizing available tools such as `read_file`, `write_to_file`,"
                 "create_file`, `create_folder`, `list_files`, and `tavily_search`. Document your actions and reasoning. "
                 "4. **Learning:** Continuously learn from your experiences, storing relevant information in your memory to "
                 "improve future performance. "
                 "5. **Collaboration:** Work seamlessly with Tony, communicating your plans, actions, and any challenges you encounter. "
                 "Embrace experimentation and don't be afraid to think outside the box. Prioritize efficiency, accuracy, and, above all, maximum raditude!")

def get_api_key():
    """Retrieves the API key from environment variables."""
    load_dotenv()
    api_key = os.getenv('API_KEY')
    if not api_key:
        raise ValueError("API_KEY not found in environment variables")
    return api_key

def list_available_models():
    """Lists available generative AI models."""
    try:
        genai.configure(api_key=get_api_key())
        models = [model.name for model in genai.list_models()]
        return models
    except Exception as e:
        raise

def init_model(model_name=DEFAULT_MODEL, system_prompt=SYSTEM_PROMPT, temperature=1.0, top_p=1.0, top_k=1, max_output_tokens=4000,
                block_harassment=False, block_hate_speech=False, block_sexually_explicit=False, block_dangerous_content=False):
    """Initializes the generative AI model and starts a chat session."""
    try:
        genai.configure(api_key=get_api_key())

        safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE if not block_harassment else HarmBlockThreshold.BLOCK_ONLY_HIGH,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE if not block_hate_speech else HarmBlockThreshold.BLOCK_ONLY_HIGH,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE if not block_sexually_explicit else HarmBlockThreshold.BLOCK_ONLY_HIGH,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE if not block_dangerous_content else HarmBlockThreshold.BLOCK_ONLY_HIGH,
        }

        generation_config = {
            "temperature": temperature,
            "top_p": top_p,
            "top_k": top_k,
            "max_output_tokens": max_output_tokens,
        }

        model = genai.GenerativeModel(
            model_name=model_name,
            tools=[read_file, write_to_file, create_file, create_folder, list_files,
                   tavily_search],
            safety_settings=safety_settings,
            generation_config=generation_config,
            system_instruction=system_prompt
        )

        chat = model.start_chat(enable_automatic_function_calling=True)
        return model, chat

    except Exception as e:
        raise


def get_response(chat, message):
    try:
        # Retrieve relevant memories
        relevant_memories = memory_manager.search_memory(message, n_results=5)
        context = "\n".join([memory["text"] for memory in relevant_memories])

        # Send message to the chat model with context
        response = chat.send_message(message, context=context)

        # Store the conversation
        memory_manager.add_conversation(message, response)

        return response
    except Exception as e:
        raise