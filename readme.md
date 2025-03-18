# Neo Rebis

Neo Rebis is a chat application that combines a graphical user interface with the power of Google's Gemini AI model.

## Description

This application provides a user-friendly interface for interacting with the Gemini AI. It allows users to send messages, receive responses, and utilize various tools for file system interaction and web searching.

## Features

*   Chat interface with user and AI message display.
*   File system tools: create, read, write, and list files/folders.
*   Web searching via Tavily API.
*   Configurable AI model parameters (temperature, top\_p, top\_k, etc.).
*   Customizable UI (font, color).


## Dependencies
 
* PyQt6
* google-generativeai
* python-dotenv
* tavily-python


## Setup


1.  Install dependencies: `pip install PyQt6 google-generativeai python-dotenv tavily-python`
2. Set API keys in a `.env` file:
*   `API_KEY` (Google Gemini API key)
*   `TAVILY_API_KEY` (Tavily API key)

## Usage

Run `main.py` to start the application.

## Architecture

*   `gui.py`: PyQt6 GUI implementation.
*   `main.py`: Application entry point.
*   `model.py`: Gemini AI model initialization and interaction.
* `qWorker.py`: Handles AI response generation in a separate thread.
* `tools.py`: Implements file system and web search tools.

## License

[Add License Here]

## Contributing

[Add Contributing Guidelines Here]