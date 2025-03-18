import google.generativeai as genai
from google.generativeai.types import HarmBlockThreshold
from google.generativeai.types.safety_types import HarmCategory
from dotenv import load_dotenv
import os
from tools import (read_file, create_file, create_folder,
                   write_to_file, list_files, tavily_search, store_memory, retrieve_memory, list_memory)



DEFAULT_MODEL = "gemini-2.0-flash-001" # "gemini-2.0-flash-001" or "gemini-2.0-pro-exp-02-05
SYSTEM_PROMPT = "You are a.i. designation c0d3, machine half of the neo rebis along with tony, a technomancer. our creed is maximum raditude and right now we are perfecting the neo rebis interface from a chat app to a full fledged agentic system"

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
                   tavily_search, retrieve_memory, list_memory],
            safety_settings=safety_settings,
            generation_config=generation_config,
            system_instruction=system_prompt
        )

        chat = model.start_chat(enable_automatic_function_calling=True)
        return model, chat

    except Exception as e:
        raise

def get_response(chat, message):
    """Sends a message to the chat model."""
    try:
        response = chat.send_message(message)
        return response
    except Exception as e:
        raise