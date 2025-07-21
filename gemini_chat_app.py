import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import simpledialog
import os
from google import genai
import sys
try:
    # Attempt to import necessary pywin32 modules
    import win32gui
    import win32con
    import struct
    # Flag to indicate if flashing is supported (Windows and pywin32 installed)
    _FLASH_WINDOW_SUPPORTED = sys.platform == 'win32'
except ImportError:
    # If pywin32 is not installed, disable flashing
    _FLASH_WINDOW_SUPPORTED = False
    # Optional: Print a warning once at startup if you want
    # print("Warning: 'pywin32' not installed. Taskbar flashing feature is disabled.")


class GeminiChatSession:
    """
    Encapsulates a Gemini chat session.
    """
    def __init__(self, api_key, model):
        """
        Initializes a new Gemini chat session.

        Args:
            api_key (str): The Google Gemini API key.
            model (str): The Gemini model to use.
        """
        self.api_key = api_key
        self.model = model
        self.client = genai.Client(api_key=api_key)
        self.chat = self.client.chats.create(model=model)
        self.token_count = 0

    def send_message_to_Gemini_API(self, prompt):
        """
        Sends a new prompt to the Gemini chat session and returns the response text, updates the token count

        Args:
            prompt (str): The user prompt.
        Returns:
            str: The AI's reply text or None if there was an error.
        """
        try:
            response = self.chat.send_message(prompt)
            self.token_count = response.usage_metadata.total_token_count
            return response.text
        except Exception as e:
            print(f"Error during Gemini API request: {e}")
            return None


class Conversation:
    """
    Encapsulates a single chat conversation.
    """
    def __init__(self, api_key, name="New Conversation", model="gemini-2.0-flash"):
        self.name = name
        self.chat_history = []  # Store message dictionaries: {'role': 'user/model', 'message_text': 'full message text'}
        self.gemini_chat_session = GeminiChatSession(api_key, model)

    def send_message(self, prompt):
        """
        Sends a message to the Gemini chat session, updates the conversation history and returns the response.
        Uses the API key associated with this conversation.

        Args:
            prompt (str): The user prompt.
        Returns:
            str: The AI's reply text, or None if there was an error.
        """
        try:
            ai_reply_text = self.gemini_chat_session.send_message_to_Gemini_API(prompt)
            if ai_reply_text:
                self.chat_history.append({"role": "user", "message_text": prompt})
                self.chat_history.append({"role": "model", "message_text": ai_reply_text})
                return ai_reply_text
            else:
                return None
        except Exception as e:
            print(f"Error sending message in Conversation: {e}")
            return None

    def get_api_key(self):
        """Returns the API key associated with this conversation."""
        return self.gemini_chat_session.api_key

    def get_model_name(self):
        """Returns the AI model name associated with this conversation."""
        return self.gemini_chat_session.model

    def get_history(self):
        """Returns the chat history for this conversation."""
        return self.chat_history


def _read_api_key_from_file():
    """
    Reads the Gemini API key from the Gemini_API_key.txt file.
    Returns the API key if successful, None otherwise.
    """
    api_key_file = "Gemini_API_key.txt"
    try:
        filepath = os.path.join(os.path.dirname(__file__), api_key_file) # Ensure file is in the same directory
        with open(filepath, "r") as f:
            key = f.readline().strip()
            if key:
                return key
            else:
                print(f"Warning: API key file '{api_key_file}' is empty.")
                return None
    except FileNotFoundError:
        print(f"Warning: API key file '{api_key_file}' not found. User will be prompted to enter it.")
        return None
    except Exception as e:
        print(f"Error reading API key from file '{api_key_file}': {e}")
        return None


class NewConversationDialog(tk.Toplevel):
    """
    A dialog window for creating a new conversation.
    Asks for API Key (loads from text file if provided), Model Selection, and Conversation Name.
    """
    def __init__(self, parent, style, initial_api_key=None, default_name="New Conversation"):
        super().__init__(parent)
        self.parent = parent
        self.style = style
        self.initial_api_key = initial_api_key
        self.default_name = default_name
        self.result = None  # Store (api_key, model_name, conversation_name) or None if cancelled

        self.title("New Conversation Settings")
        self.transient(parent) # Keep on top of parent
        self.grab_set()        # Make modal
        self.resizable(False, False)

        # Apply background color from style
        popup_bg = self.style.lookup('.', 'background')
        self.config(bg=popup_bg, padx=15, pady=15)

        # --- Variables ---
        self.api_key_var = tk.StringVar(value=self.initial_api_key or "")
        self.model_var = tk.StringVar()
        self.name_var = tk.StringVar(value=self.default_name)
        self.status_var = tk.StringVar(value="") # For loading messages

        # --- Widgets ---
        # API Key Entry
        ttk.Label(self, text="API Key:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        self.api_key_entry = ttk.Entry(self, textvariable=self.api_key_var, width=50)
        self.api_key_entry.grid(row=0, column=1, columnspan=2, sticky=tk.EW, pady=(0, 5))

        # Model Combobox
        ttk.Label(self, text="Model:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.model_combobox = ttk.Combobox(self, textvariable=self.model_var, state="readonly", width=47)
        self.model_combobox.grid(row=1, column=1, sticky=tk.EW, pady=5)
        self.load_models_button = ttk.Button(self, text="Load Models", command=self._load_models)
        self.load_models_button.grid(row=1, column=2, sticky=tk.E, padx=(5, 0), pady=5)

        # Conversation Name Entry
        ttk.Label(self, text="Conversation Name:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.name_entry = ttk.Entry(self, textvariable=self.name_var, width=50)
        self.name_entry.grid(row=2, column=1, columnspan=2, sticky=tk.EW, pady=5)
        self.name_entry.focus_set() # Start typing here
        self.name_entry.select_range(0, tk.END)

        # Status Label
        self.status_label = ttk.Label(self, textvariable=self.status_var, foreground="orange")
        self.status_label.grid(row=3, column=0, columnspan=3, sticky=tk.W, pady=(5, 10))

        # Buttons Frame
        button_frame = ttk.Frame(self)
        button_frame.grid(row=4, column=0, columnspan=3, pady=(10, 0))

        self.ok_button = ttk.Button(button_frame, text="OK", command=self._on_ok, state=tk.DISABLED) # Disabled initially
        self.ok_button.pack(side=tk.RIGHT, padx=(10, 0))
        self.cancel_button = ttk.Button(button_frame, text="Cancel", command=self._on_cancel)
        self.cancel_button.pack(side=tk.RIGHT)

        self.update_idletasks() # Ensure widgets are sized

        # Center the dialog
        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        parent_w = parent.winfo_width()
        parent_h = parent.winfo_height()
        dialog_w = self.winfo_reqwidth()
        dialog_h = self.winfo_reqheight()
        center_x = parent_x + (parent_w // 2) - (dialog_w // 2)
        center_y = parent_y + (parent_h // 2) - (dialog_h // 2)
        self.geometry(f"+{center_x}+{center_y}")

        # Try loading models immediately if key is provided in text file
        if self.initial_api_key:
            self._load_models()

        self.protocol("WM_DELETE_WINDOW", self._on_cancel) # Handle closing window
        self.wait_window(self) # Wait here until dialog is destroyed

    def _load_models(self):
        """Attempts to load models using the API key from the entry."""
        api_key = self.api_key_var.get().strip()
        if not api_key:
            self.status_var.set("Please enter an API Key.")
            messagebox.showerror("API Key Missing", "Please enter your Gemini API key.", parent=self)
            return

        self.status_var.set("Loading models...")
        self.update_idletasks() # Show status message
        self.load_models_button.config(state=tk.DISABLED)
        self.model_combobox.set('') # Clear previous selection/values
        self.model_combobox.config(values=[], state=tk.DISABLED)
        self.ok_button.config(state=tk.DISABLED)

        available_models = []
        try:
            # Use a temporary client to list models
            temp_client = genai.Client(api_key=api_key)
            for m in temp_client.models.list():
                available_models.append(m.name)

            if not available_models:
                raise Exception("No models found.") # Raise exception if models list is empty

            self.model_combobox.config(values=available_models, state="readonly")

            # Pre-select the first available one
            self.model_combobox.current(0)

            self.ok_button.config(state=tk.NORMAL) # Enable OK if models loaded
            self.status_var.set("Models loaded successfully.")

        except Exception as e:
            error_msg = f"Error loading models: {e}"
            print(error_msg) # Log the error
            self.status_var.set("Failed to load models. Check API key and connection.")
            messagebox.showerror("Model Loading Error", error_msg, parent=self)
            # Keep OK disabled
        finally:
            self.load_models_button.config(state=tk.NORMAL) # Re-enable button

    def _on_ok(self):
        """Validates input and stores results before closing."""
        api_key = self.api_key_var.get().strip()
        model_name = self.model_var.get()
        conversation_name = self.name_var.get().strip()

        if not api_key:
            messagebox.showerror("Input Error", "API Key cannot be empty.", parent=self)
            return
        if not model_name:
            messagebox.showerror("Input Error", "Please select a model.", parent=self)
            return
        if not conversation_name:
            messagebox.showerror("Input Error", "Conversation Name cannot be empty.", parent=self)
            return

        self.result = (api_key, model_name, conversation_name)
        self.destroy()

    def _on_cancel(self):
        """Sets result to None and closes the dialog."""
        self.result = None
        self.destroy()


class AIChatApp:
    def __init__(self, root):
        self.root = root
        root.title("LLM AI Chat App (Gemini)")

        # --- Style Setup ---
        self.style = ttk.Style(root)
        self._setup_dark_theme()

        self.provider = tk.StringVar(value="Gemini")  # Fixed to Gemini
        self.conversations = []  # List to hold Conversation instances
        self.active_conversation = None  # Currently selected Conversation object
        self.conversation_names = tk.StringVar()  # For Combobox values
        self.conversation_name_list = []  # List of conversation names for Combobox
        self.conversation_ids = {}  # Dictionary to store conversation name -> list of message node IDs
        self.message_node_to_content = {}  # Dictionary to map Treeview message node IDs to full message content
        self.conversation_counter = 1  # Counter for conversation names
        self.current_conversation_api_key_display = tk.StringVar(value="API Key: N/A")  # For API Key display label
        self.waiting_popup = None # To hold the waiting popup window
        self.model_selection_dialog = None # To hold the model selection popup window
        self.total_tokens_used_display = tk.StringVar(value="Tokens: N/A")
        self.model_name_display = tk.StringVar(value="Model: N/A")
        self.selected_message_token_count_var = tk.StringVar(value="")
        self.prompt_token_count_var = tk.StringVar(value="Tokens: 0")

        self._create_widgets()

        self.root.state('zoomed')  # Maximize window

    def _setup_dark_theme(self):
        """Configures ttk styles for a dark theme."""
        # Define dark theme colors
        BG_COLOR = '#2E2E2E'
        FG_COLOR = '#EAEAEA'
        SELECT_BG = '#4A4A4A'  # Background for selected items/hover
        SELECT_FG = '#FFFFFF'
        WIDGET_BG = '#3C3C3C'  # Background for widgets like buttons, entries
        TEXT_FG = '#FFFFFF'  # Text color for most widgets
        DISABLED_FG = '#777777'  # Color for disabled text/widgets
        TREEVIEW_HEADING_BG = '#3C3C3C'
        TREEVIEW_FIELD_BG = '#383838'  # Background of the treeview item area
        AI_MSG_BG = '#203A20'  # Dark green background for AI messages in Treeview

        # --- Store colors needed later for tk widgets or tags ---
        self.bg_color = BG_COLOR
        self.fg_color = FG_COLOR
        self.widget_bg_color = WIDGET_BG
        self.text_fg_color = TEXT_FG
        self.text_bg_color = WIDGET_BG
        self.select_bg_color = SELECT_BG
        self.select_fg_color = SELECT_FG
        self.text_insert_color = FG_COLOR  # Cursor color
        self.ai_msg_bg_color = AI_MSG_BG

        try:
            # Attempt to use 'clam' theme which is often more customizable
            self.style.theme_use('clam')
        except tk.TclError:
            print("Theme 'clam' not available, using default.")

        # Global style configurations
        self.style.configure('.',
                             background=BG_COLOR,
                             foreground=FG_COLOR,
                             fieldbackground=WIDGET_BG,  # Default field bg
                             troughcolor=BG_COLOR)  # Scrollbar trough

        # Specific widget styles
        self.style.configure('TFrame', background=BG_COLOR)
        self.style.configure('TLabel', background=BG_COLOR, foreground=FG_COLOR)
        self.style.configure('TButton', background=WIDGET_BG, foreground=TEXT_FG)
        self.style.map('TButton',
                       background=[('active', SELECT_BG), ('disabled', BG_COLOR)],
                       foreground=[('active', SELECT_FG), ('disabled', DISABLED_FG)])

        self.style.configure('TCombobox',
                             fieldbackground=WIDGET_BG,
                             background=WIDGET_BG,
                             foreground=TEXT_FG,
                             arrowcolor=FG_COLOR,
                             selectbackground=SELECT_BG,  # Selection color in dropdown
                             selectforeground=SELECT_FG)
        # Map ensures hover/focus looks right if theme supports it
        self.style.map('TCombobox', fieldbackground=[('readonly', WIDGET_BG)],
                       selectbackground=[('readonly', SELECT_BG)],
                       selectforeground=[('readonly', SELECT_FG)])

        self.style.configure('Treeview',
                             background=TREEVIEW_FIELD_BG,
                             foreground=FG_COLOR,
                             fieldbackground=TREEVIEW_FIELD_BG,  # Item area background
                             rowheight=25)  # Adjust if needed
        self.style.configure('Treeview.Heading',
                             background=TREEVIEW_HEADING_BG,
                             foreground=FG_COLOR,
                             relief='flat')
        self.style.map('Treeview.Heading',
                       background=[('active', SELECT_BG)])  # Hover/click on heading

        # Configure Treeview selection style
        self.style.map('Treeview',
                       background=[('selected', SELECT_BG)],
                       foreground=[('selected', SELECT_FG)])

        # Configure PanedWindow sash (the divider)
        self.style.configure('TPanedwindow', background=BG_COLOR)
        self.style.configure('Sash', background=WIDGET_BG, sashthickness=6, relief='raised')

    def _create_widgets(self):
        """Creates and lays out all the main widgets by calling helper methods."""
        # --- Apply root background color ---
        self.root.config(bg=self.style.lookup('.', 'background'))

        # --- Conversation Selection Frame (Top of Window) ---
        self._create_conversation_controls(self.root)

        # --- PanedWindow for Left-to-Right Layout ---
        self.paned_window = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # --- Create Panels and add them to the PanedWindow ---
        self._create_messages_panel(self.paned_window)
        self._create_message_display_panel(self.paned_window)
        self._create_prompt_panel(self.paned_window)

    # --- Helper Methods for Widget Creation ---

    def _create_conversation_controls(self, parent):
        """Creates the top bar controls for conversation management."""
        self.conversation_select_frame = ttk.Frame(parent)
        self.conversation_select_frame.pack(pady=5, padx=5, fill=tk.X)

        ttk.Label(self.conversation_select_frame, text="Active Conversation:").pack(side=tk.LEFT, padx=5)
        self.conversation_combobox = ttk.Combobox(self.conversation_select_frame, textvariable=self.conversation_names,
                                                  values=self.conversation_name_list, state="readonly", width=30)
        self.conversation_combobox.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=False)
        self.conversation_combobox.bind("<<ComboboxSelected>>", self._on_conversation_combobox_select)

        self.new_conversation_button = ttk.Button(self.conversation_select_frame, text="New Conversation",
                                                  command=self._add_new_conversation)
        self.new_conversation_button.pack(side=tk.LEFT, padx=5)

        # Pack status labels to the right
        self.model_name_label = ttk.Label(self.conversation_select_frame, textvariable=self.model_name_display)
        self.model_name_label.pack(side=tk.RIGHT, padx=(10, 20))

        self.token_info_label = ttk.Label(self.conversation_select_frame, textvariable=self.total_tokens_used_display)
        self.token_info_label.pack(side=tk.RIGHT, padx=(10, 10))

        self.api_key_label = ttk.Label(self.conversation_select_frame,
                                       textvariable=self.current_conversation_api_key_display)
        self.api_key_label.pack(side=tk.RIGHT, padx=(10, 10))

    def _create_messages_panel(self, parent_pane):
        """Creates the left panel with the message list (Treeview)."""
        messages_frame = ttk.Frame(parent_pane, padding=5)
        parent_pane.add(messages_frame, weight=1) # Weight for resizing

        ttk.Label(messages_frame, text="Messages").pack(pady=(0, 5), anchor=tk.W)

        # Frame to hold treeview and scrollbar together
        tree_frame = ttk.Frame(messages_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        self.messages_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL)
        self.messages_tree = ttk.Treeview(tree_frame, show="tree",
                                          yscrollcommand=self.messages_scrollbar.set) # Link treeview to scrollbar
        self.messages_scrollbar.config(command=self.messages_tree.yview) # Link scrollbar to treeview

        # Pack scrollbar first, then treeview
        self.messages_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.messages_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True) # Pack treeview to fill remaining space

        self.messages_tree.bind("<<TreeviewSelect>>", self._on_treeview_message_select)
        self.messages_tree.tag_configure("ai_message",
                                         background=self.ai_msg_bg_color,
                                         foreground=self.fg_color)

    def _create_message_display_panel(self, parent_pane):
        """Creates the middle panel for displaying the selected message content."""
        message_frame = ttk.Frame(parent_pane, padding=5)
        parent_pane.add(message_frame, weight=2) # Weight for resizing

        # Frame to hold the title row widgets horizontally
        message_title_frame = ttk.Frame(message_frame)
        message_title_frame.pack(fill=tk.X, pady=(0, 5)) # Anchor title West

        ttk.Label(message_title_frame, text="Message").pack(side=tk.LEFT, padx=(0, 5))

        self.copy_message_button = ttk.Button(message_title_frame, text="Copy",
                                              command=self._copy_message_text)
        self.copy_message_button.pack(side=tk.LEFT, padx=(0, 10))

        self.token_count_display_label = ttk.Label(message_title_frame,
                                                   textvariable=self.selected_message_token_count_var)
        # Pack token count to the right end of the title frame
        self.token_count_display_label.pack(side=tk.RIGHT, padx=(10, 0))

        # Frame to hold text and scrollbar
        text_frame = ttk.Frame(message_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)

        self.message_scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL)
        self.message_text = tk.Text(text_frame, wrap=tk.WORD, state=tk.DISABLED,
                                    bg=self.text_bg_color, fg=self.text_fg_color,
                                    borderwidth=0, relief='flat',
                                    insertbackground=self.text_insert_color,
                                    yscrollcommand=self.message_scrollbar.set) # Link text widget to scrollbar
        self.message_scrollbar.config(command=self.message_text.yview) # Link scrollbar to text widget

        # Pack scrollbar first, then text widget
        self.message_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.message_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True) # Pack text to fill remaining space

    def _create_prompt_panel(self, parent_pane):
        """Creates the right panel for user prompt input."""
        prompt_frame = ttk.Frame(parent_pane, padding=5)
        parent_pane.add(prompt_frame, weight=1) # Weight for resizing

        # Frame to hold the prompt title row widgets horizontally
        prompt_title_frame = ttk.Frame(prompt_frame)
        prompt_title_frame.pack(fill=tk.X, pady=(0, 5)) # Anchor title West

        ttk.Label(prompt_title_frame, text="Prompt").pack(side=tk.LEFT, padx=(0, 5))

        # Pack Update Count button and label to the right
        self.update_prompt_tokens_button = ttk.Button(prompt_title_frame, text="Update Count",
                                                      command=self._update_prompt_token_count)
        self.update_prompt_tokens_button.pack(side=tk.RIGHT, padx=(5, 0))

        self.prompt_token_count_label = ttk.Label(prompt_title_frame, textvariable=self.prompt_token_count_var)
        self.prompt_token_count_label.pack(side=tk.RIGHT, padx=(10, 5))

        # Create a sub-frame for the prompt editor and its scrollbar
        prompt_editor_frame = ttk.Frame(prompt_frame)
        prompt_editor_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))

        self.prompt_scrollbar = ttk.Scrollbar(prompt_editor_frame, orient=tk.VERTICAL)
        self.prompt_text_editor = tk.Text(prompt_editor_frame, wrap=tk.WORD,
                                          bg=self.text_bg_color, fg=self.text_fg_color,
                                          borderwidth=0, relief='flat',
                                          insertbackground=self.text_insert_color,
                                          yscrollcommand=self.prompt_scrollbar.set) # Link text editor to scrollbar
        self.prompt_scrollbar.config(command=self.prompt_text_editor.yview) # Link scrollbar to text editor

        # Pack scrollbar first, then text editor
        self.prompt_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.prompt_text_editor.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Button to send the prompt (below the editor frame)
        self.send_button = ttk.Button(prompt_frame, text="Send", command=self.send_prompt)
        self.send_button.pack(pady=5)

    def _insert_message_to_treeview(self, role, message_content):
        """
        Inserts a message into the messages_tree with role, truncated text, and appropriate tags.

        Args:
            role (str): 'user' or 'model', indicating the sender.
            message_content (str): The full message text.

        Returns:
            str: The node ID of the inserted message in the Treeview.
        """

        tags = ()  # Default tag is empty tuple
        if role == 'model': # If it's AI message
            tags = "ai_message" # Add 'ai_message' tag for background

        # Conditional truncation logic
        display_text = message_content
        if len(message_content) > 20:
            display_text = message_content[:20] + "..."

        node_id = self.messages_tree.insert("", tk.END, text=f"{role.capitalize()}: {display_text}", tags=tags)
        return node_id

    def send_prompt(self):
        prompt_text = self.prompt_text_editor.get("1.0", tk.END).strip()

        if not prompt_text:
            messagebox.showerror("Prompt Required", "Please enter a prompt.")
            return
        if not self.active_conversation: # Check if active conversation is selected
            messagebox.showerror("Conversation Required", "Please select an active conversation.")
            return

        self._show_waiting_popup() # Show the waiting popup

        ai_reply_text = self.active_conversation.send_message(prompt_text)  # Use conversation's API key

        if self.waiting_popup: # Check if popup exists before destroying (should not happen)
            self.waiting_popup.destroy() # Close the waiting popup after response is received
            self.waiting_popup = None # Reset to None

        if ai_reply_text:
            # Add user prompt and AI reply to Treeview
            current_conversation_name = self.conversation_combobox.get()  # Get conversation name from combobox
            if not current_conversation_name:  # Should not happen as combobox is readonly, but for safety
                print("Error: No active conversation name found in combobox.")
                self.total_tokens_used_display.set("Tokens: Error") # Update status on error
                return

            # Use _insert_message_to_treeview to add messages and get node IDs
            user_message_node_id = self._insert_message_to_treeview("user", prompt_text) # Insert user message
            ai_message_node_id = self._insert_message_to_treeview("model", ai_reply_text) # Insert AI reply

            if current_conversation_name not in self.conversation_ids:
                self.conversation_ids[current_conversation_name] = [] # Initialize list if conversation name is new (though it should exist)

            self.conversation_ids[current_conversation_name].append(user_message_node_id)  # Store message node ID
            self.conversation_ids[current_conversation_name].append(ai_message_node_id)  # Store message node ID

            # Store full message content associated with Treeview node IDs
            self.message_node_to_content[user_message_node_id] = {"role": "user", "message_text": prompt_text}
            self.message_node_to_content[ai_message_node_id] = {"role": "model", "message_text": ai_reply_text}

            self.prompt_text_editor.delete("1.0", tk.END) # clear prompt text editor after sending
            self.prompt_token_count_var.set("Tokens: 0")  # Reset prompt token counter after sending

            self._update_token_count_display()

        else:
            messagebox.showerror("Gemini Error", "Failed to get response from Gemini.\n"
                                                 "Please check API key and network connection "
                                                 "(see console for details).")
            self.total_tokens_used_display.set("Tokens: Error") # Update token count display on error
            if self.waiting_popup: # Ensure popup is closed even in error case
                self.waiting_popup.destroy()
                self.waiting_popup = None

        self._flash_window()

    def _flash_window(self):
        """Flashes the window in the taskbar on Windows if supported and not foreground."""
        if not _FLASH_WINDOW_SUPPORTED:
            return

        try:
            # Get the top-level window handle
            hwnd_main_frame = int(self.root.winfo_id())
            hwnd = win32gui.GetAncestor(hwnd_main_frame, win32con.GA_ROOT)
            if hwnd == 0:
                hwnd = hwnd_main_frame

            # Check if window is already in foreground
            foreground_hwnd = win32gui.GetForegroundWindow()
            if hwnd == foreground_hwnd:
                return  # Don't flash if already active

            # Flags: Flash taskbar and window caption, continuously until focus
            flags = win32con.FLASHW_ALL | win32con.FLASHW_TIMERNOFG
            # Count: Set to 0 when using FLASHW_TIMERNOFG
            count = 0
            # Timeout: 0 uses default cursor blink rate
            timeout = 0

            # Call FlashWindowEx
            win32gui.FlashWindowEx(hwnd, flags, count, timeout)

        except Exception as e:
            print(f"Warning: Could not flash window taskbar icon: {e}")

    def _display_message(self, message):
        """
        Displays a message in the Message display area.

        Args:
            message (str): The message text.
        """
        self.message_text.config(state=tk.NORMAL)  # Enable editing to insert
        self.message_text.delete("1.0", tk.END)  # Clear previous message
        self.message_text.insert("1.0", message)  # Insert new message
        self.message_text.config(state=tk.DISABLED)  # Disable editing

    def _on_treeview_message_select(self, event):
        """
        Handles the event when a message is selected in the Treeview.
        Displays the selected message in the Message Text area.
        """

        selected_item = self.messages_tree.selection()
        if not selected_item:
            self._clear_message_display()  # Clears text
            return  # Nothing selected

        selected_node_id = selected_item[0]

        # Find and display the message content.
        if selected_node_id in self.message_node_to_content:
            message_content = self.message_node_to_content[selected_node_id]['message_text'] # Get full message from dict
            self._display_message(message_content) # Display the full message

            # Token counting
            if self.active_conversation and self.active_conversation.gemini_chat_session.client:
                try:
                    client = self.active_conversation.gemini_chat_session.client
                    model_name = self.active_conversation.get_model_name()
                    token_count = client.models.count_tokens(model=model_name, contents=message_content).total_tokens
                    token_info_text = f"Tokens: {token_count}"  # Set text for the token count label

                except Exception as e:
                    print(f"Error counting tokens for selected message: {e}")
                    token_info_text = "Tokens: Error"  # Set error text for the token count label
            else:
                token_info_text = "Tokens: N/A"  # Indicate if client/conversation unavailable

        else:
            # Fallback in case message content is not found
            self._display_message("Error: Message content not found.")
            token_info_text = "Tokens: Error"

        # Update the token count label text
        self.selected_message_token_count_var.set(token_info_text)

    def _on_active_conversation_change(self):
        """
        Should be called when active conversation changes (new conversation added or different conversation selected)
        # Updates the GUI elements that display info about the active conversation
        """

        self._display_conversation_in_treeview(self.active_conversation)  # Update Treeview to show the messages of the new active conversation
        self._update_api_key_display(self.active_conversation)
        self._update_token_count_display()

        # Update model name display
        model_name = self.active_conversation.get_model_name()
        model_str = f"Model: {model_name}"
        self.model_name_display.set(model_str)

        # Recalculate the token count of the current prompt editor text (the model potentially changed)
        self._update_prompt_token_count()

    def _on_conversation_combobox_select(self, event):
        """
        Handles the event when a conversation is selected in the Combobox.
        Sets the active_conversation to the selected Conversation object calls the method to update relevant GUI info.
        """
        selected_conversation_name = self.conversation_combobox.get()
        for conv in self.conversations:
            if conv.name == selected_conversation_name:
                self.active_conversation = conv
                self._on_active_conversation_change()
                break # Exit loop once found and processed

    def _add_new_conversation(self):
        """
        Opens a unified dialog to get API key, model, and name for a new conversation,
        then creates and activates it.
        """
        initial_api_key = _read_api_key_from_file() # Try to read API key from file first

        # Create and show the New Conversation dialog
        dialog = NewConversationDialog(self.root, self.style,
                                       initial_api_key=initial_api_key,
                                       default_name=f"Conversation {self.conversation_counter}")

        # Dialog waits here until closed. Get the result.
        dialog_result = dialog.result

        if not dialog_result:
            return # User cancelled or closed the dialog

        # Unpack results if OK was clicked
        api_key, model_name, conversation_name = dialog_result

        # Check for duplicate conversation name
        # Get a list of current conversation names
        existing_names = [conv.name for conv in self.conversations]

        # Check if the proposed name already exists
        if conversation_name in existing_names:
            messagebox.showerror("Duplicate Name",
                                 f"A conversation named '{conversation_name}' already exists.\n\n"
                                 "Please try creating a new conversation with a unique name.",
                                 parent=self.root) # If proposed name already exists, make error messagebox appear
            return # Stop the process, do not create the conversation

        # Create the conversation object
        try:
            new_conversation = Conversation(api_key, conversation_name, model_name)
            # Test the connection implicitly by checking the GeminiChatSession
            if not new_conversation.gemini_chat_session: # Check if session creation failed
                raise Exception("Failed to initialize Gemini session (check API key/model).")

        except Exception as e:
            messagebox.showerror("Conversation Error", f"Could not create conversation:\n{e}", parent=self.root)
            return # Stop if creation failed

        # Add to list and update UI
        self.conversations.append(new_conversation)
        self.conversation_counter += 1 # Increment counter for next default name suggestion

        self._update_conversation_combobox() # Update Combobox with new conversation names
        self.conversation_combobox.set(new_conversation.name) # Set Combobox to the new conversation

        # Set the new conversation as active and update GUI info
        self.active_conversation = new_conversation
        self._on_active_conversation_change()

    def _update_conversation_combobox(self):
        """
        Updates the Combobox with the current list of conversation names.
        """
        self.conversation_name_list = [conv.name for conv in self.conversations] # Extract names
        self.conversation_combobox['values'] = self.conversation_name_list # Update Combobox values
        if self.conversation_name_list:
            self.conversation_combobox.current(0) # Optionally select the first one by default if list is not empty

    def _display_conversation_in_treeview(self, conversation):
        """
        Displays a conversation's messages in the Treeview, clearing previous content and Message display.
        """
        self.messages_tree.delete(*self.messages_tree.get_children()) # Clear Treeview
        self.message_node_to_content = {} # Clear message content dictionary when redrawing conversation
        self._clear_message_display() # Clear Message display area when switching conversations

        conversation_name = conversation.name # Get conversation name to use as key for conversation_ids
        self.conversation_ids[conversation_name] = [] # Ensure conversation_ids has an entry for this conversation

        history = conversation.get_history()
        for message in history:
            role = message['role']
            message_text = message['message_text']

            # Use _insert_message_to_treeview to add messages and get node IDs
            message_node_id = self._insert_message_to_treeview(role, message_text)

            self.conversation_ids[conversation_name].append(message_node_id) # Store message node ID under conversation name
            self.message_node_to_content[message_node_id] = message # Store full message content

    def _clear_message_display(self):
        """Clears the Message display area."""
        self.message_text.config(state=tk.NORMAL)
        self.message_text.delete("1.0", tk.END)
        self.message_text.config(state=tk.DISABLED)
        self.selected_message_token_count_var.set("")

    def _update_api_key_display(self, conversation):
        """Updates the API key display label below the Combobox."""
        if conversation and conversation.get_api_key():
            self.current_conversation_api_key_display.set(f"API Key: {conversation.get_api_key()}")
        else:
            self.current_conversation_api_key_display.set("API Key: N/A")

    def _update_token_count_display(self):
        # Updates the token count display with the token count of the active conversation
        tokens_used = self.active_conversation.gemini_chat_session.token_count
        token_str = f"Tokens in context: {tokens_used}"
        self.total_tokens_used_display.set(token_str)

    def _show_waiting_popup(self):
        """
        Creates and displays the "Waiting for response.." popup window centered
        on the main application window.
        """
        self.waiting_popup = tk.Toplevel(self.root)
        self.waiting_popup.title("Please Wait")
        self.waiting_popup.transient(self.root) # Keep popup on top of main window
        self.waiting_popup.grab_set() # Make popup modal

        # Use colors from the style/theme
        popup_bg = self.style.lookup('.', 'background')
        # Configure Toplevel background
        self.waiting_popup.config(bg=popup_bg, borderwidth=1, relief="solid")

        wait_label = ttk.Label(self.waiting_popup, text="Waiting for response..", padding=10)
        wait_label.pack()
        self.waiting_popup.config(borderwidth=2, relief="solid")

        self.waiting_popup.update_idletasks() # Update to get correct window size

        # Get main window position and size
        main_window_width = self.root.winfo_width()
        main_window_height = self.root.winfo_height()
        main_window_x = self.root.winfo_x()
        main_window_y = self.root.winfo_y()

        # Get popup window size
        popup_width = self.waiting_popup.winfo_reqwidth()
        popup_height = self.waiting_popup.winfo_reqheight()

        # Calculate centering position
        center_x = main_window_x + (main_window_width // 2) - (popup_width // 2)
        center_y = main_window_y + (main_window_height // 2) - (popup_height // 2)

        # Set popup position
        self.waiting_popup.geometry(f"+{center_x}+{center_y}")

        wait_label.update()
        self.waiting_popup.update()
        self.root.update_idletasks() # Ensure main root is also updated

    def _update_prompt_token_count(self):
        """
        Calculates and updates the token count label for the prompt text editor.
        Triggered by the Update Count button.
        """
        try:
            prompt_text = self.prompt_text_editor.get("1.0", tk.END).strip()

            if not prompt_text:
                self.prompt_token_count_var.set("Tokens: 0")
                return

            if self.active_conversation and self.active_conversation.gemini_chat_session.client:
                client = self.active_conversation.gemini_chat_session.client
                model_name = self.active_conversation.get_model_name()
                try:
                    token_response = client.models.count_tokens(model=model_name, contents=prompt_text)
                    token_count = token_response.total_tokens
                    self.prompt_token_count_var.set(f"Tokens: {token_count}")
                except Exception as e:
                    print(f"Error counting prompt tokens: {e}")
                    self.prompt_token_count_var.set("Tokens: Error")
            else:
                # No active conversation or client not available
                self.prompt_token_count_var.set("Tokens: N/A")

        except Exception as e:
            print(f"Unexpected error updating prompt token count: {e}")
            self.prompt_token_count_var.set("Tokens: Error")

    def _copy_message_text(self):
        """Copies the content of the message_text display area to the clipboard."""
        try:
            # Get text from the Text widget (works even if state is DISABLED)
            text_to_copy = self.message_text.get("1.0", tk.END).strip()
            if text_to_copy:
                self.root.clipboard_clear()  # Clear the clipboard first
                self.root.clipboard_append(text_to_copy) # Append the text
            else:
                print("Nothing to copy.")
        except tk.TclError:
            # This might happen if the clipboard is unavailable
            messagebox.showerror("Clipboard Error", "Could not access the system clipboard.")
        except Exception as e:
            print(f"Error copying message text: {e}")
            messagebox.showerror("Error", f"An unexpected error occurred during copy:\n{e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = AIChatApp(root)
    root.mainloop()