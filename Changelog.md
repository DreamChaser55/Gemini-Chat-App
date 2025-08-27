Gemini AI Chat app changelog:

## Version 0.5

### Added
- **Keyboard Shortcut:** You can now press `Ctrl+Enter` in the prompt editor to send your message, providing a faster alternative to clicking the "Send" button.

### Changed
- **Performance Optimization:** Implemented caching for message token counts. The app now only requests the token count for a message from the API once, improving performance and reducing API calls when re-selecting messages.
- **Window Maximization:** The application now uses a more robust, cross-platform method to maximize the window on startup, improving compatibility with different operating systems.

### Fixed
- **Windows Notifications:** The taskbar icon flashing notification (after a response is received) is now more reliable, especially on 64-bit systems, by correctly using the `pywin32` library.

### Removed
- **Simplified Internal State:** Removed a redundant internal data structure (`conversation_ids`) used for tracking messages. This simplifies the code.

## Version 0.4

Initial commit.