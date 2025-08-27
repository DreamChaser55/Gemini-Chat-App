# Gemini AI Chat Desktop App

A desktop GUI application for interacting with Google's Gemini family of language models. Built with Python and `tkinter`, this app provides a robust and user-friendly interface for managing multiple chat conversations.

## Description

This application allows users to chat with various Gemini models through a clean, resizable, three-panel interface. It's designed to be a powerful tool for developers, writers, and anyone looking to explore the capabilities of Gemini large language models locally. You can manage separate conversations, each with its own context, API key, and model, making it easy to organize different projects and experiments.

## Features

* **Modern Dark Theme**: A sleek, easy-on-the-eyes dark interface for comfortable use.
* **Multi-Conversation Management**: Create and switch between multiple, named conversations. Each conversation maintains its own independent chat history.
* **Flexible Configuration**: Assign a different Gemini model and API key to each conversation.
* **Dynamic Model Loading**: Automatically fetches and displays a list of available Gemini models directly from the API, ensuring you always have access to the latest versions.
* **API Key Management**: For convenience, the app can read your Google Gemini API key from a local `Gemini_API_key.txt` file, or you can enter it directly in the UI.
* **Detailed Token Tracking**:
    * View the total token count for the current conversation's context.
    * See the token count for any selected message in the history.
    * Get an on-demand token count for your prompt before sending it.
* **User-Friendly Interface**:
    * A resizable three-panel layout (Message History, Message Content, Prompt Editor).
	* The leftmost Message History panel shows the list of all previous messages in the current conversation. Each message can be easily selected and viewed in the Message Content panel.
    * A "Waiting for response..." indicator prevents the UI from appearing frozen during API calls.
    * Copy message content to the clipboard with a single click.
* **Windows Taskbar Notifications**: For Windows users, the app icon will flash in the taskbar when a new message is received while the window is not in focus (requires `pywin32`).

## Requirements

* Python 3.x
* `google-genai`
* `pywin32` (Optional, for taskbar notifications on Windows)

## Installation and Usage

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/your-username/your-repository-name.git](https://github.com/your-username/your-repository-name.git)
    cd your-repository-name
    ```

2.  **Install the required packages:**
    It is recommended to use a virtual environment.
    ```bash
    # Create and activate a virtual environment (optional but recommended)
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`

    # Install dependencies
    pip install google-genai pywin32
    ```

3.  **Set up your API Key:**
    You have two options:
    * **(Recommended)** Create a file named `Gemini_API_key.txt` in the same directory as `gemini_chat_app.py`. Paste your Google Gemini API key into this file and save it.
    * Alternatively, you can leave the file out and enter your API key directly into the "New Conversation" dialog when you run the app.

4.  **Run the application:**
    ```bash
    python gemini_chat_app.py
    ```

5.  **Start Chatting:**
    * Click the "New Conversation" button.
    * If you didn't create the API key file, paste your key into the dialog.
    * Click "Load Models" to fetch the available Gemini models.
    * Select a model, give your conversation a name, and click "OK".
    * Start typing in the "Prompt" panel and click "Send" or press `Ctrl+Enter`!

## Code Structure

The application is built with an object-oriented approach to separate concerns and enhance maintainability.

* `AIChatApp`: The main class that constructs the `tkinter` GUI, manages the overall layout, and handles user interactions. It orchestrates all other components.
* `Conversation`: Represents a single, self-contained chat. It holds the message history and is associated with a specific `GeminiChatSession`.
* `GeminiChatSession`: A low-level class that encapsulates the direct communication with the Google Gemini API. It manages the API client, sends requests, and tracks token usage for a single session.
* `NewConversationDialog`: A custom `tkinter` dialog window responsible for gathering the necessary inputs (API key, model, name) from the user when creating a new conversation.

## License

All content and source code for this application are subject to the terms of the MIT License.
