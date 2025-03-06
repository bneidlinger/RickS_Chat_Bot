# Rick Sanchez AI Chatbot

A fully offline-capable AI chatbot that talks just like Rick from Rick and Morty, complete with a sci-fi Matrix-inspired UI. This project combines a PyTorch-based language model with custom personality processing to create an interactive Rick Sanchez experience.

![Rick Chatbot Screenshot](screenshot.jpg)

## Features

- 🧪 **Authentic Rick Personality**: Stuttering, burps, catchphrases, and scientific references
- 🌌 **Matrix-Inspired UI**: Green text on black with raining code effect in the background
- 💻 **Fully Offline Capable**: No API keys or internet connection required after initial setup
- 🔬 **Adaptive Responses**: Rick's mood and responses adapt to different types of questions
- 💾 **Session Management**: Multiple conversations can be maintained simultaneously

## How It Works

The chatbot combines several key components:

1. **Language Model**: Uses BlenderBot from Hugging Face to generate base responses
2. **Rick Processor**: Transforms ordinary text into Rick's distinctive speech patterns
3. **WebSocket Interface**: Real-time communication with typing indicators
4. **Themed UI**: Custom CSS and JavaScript for the Rick and Morty / Matrix aesthetic

## Installation

### Prerequisites

- Python 3.7+
- PyTorch
- Flask
- Transformers (Hugging Face)

### Setup

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/rick-chatbot.git
   cd rick-chatbot
   ```

2. Install the requirements:
   ```
   pip install -r requirements.txt
   ```

3. Run the application:
   ```
   python app.py
   ```

4. Open your browser and navigate to:
   ```
   http://localhost:5000
   ```

## Configuration

You can customize Rick's personality by modifying the `rick_config.py` file:

- Adjust stuttering frequency
- Change catchphrase probability
- Modify scientific terminology
- Tune response generation parameters

## Project Structure

- `app.py` - Main Flask application
- `rick_processor.py` - Rick speech pattern processor
- `rick_config.py` - Configuration settings
- `templates/` - HTML templates including the chat interface
- `static/` - CSS, JavaScript, and other static assets
- `model/` - Downloaded model files (created on first run)

## Usage Tips

- **Scientific Questions**: Ask Rick about physics, dimensions, or his portal gun for the best responses
- **Personal Questions**: Inquire about Morty, his family, or his adventures
- **Reset Button**: Click "Reset" to start a fresh conversation
- **Long Conversations**: The chatbot remembers context from previous messages

## Limitations

- The offline model has knowledge limitations compared to online LLMs
- Very complex questions may trigger fallback responses
- Response generation can be slow on systems without GPU acceleration

## Future Improvements

- [ ] Add voice output with Rick's speech patterns
- [ ] Implement image generation for Rick's inventions
- [ ] Create a mobile app version
- [ ] Add more character options (Morty, Summer, etc.)

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- Inspired by the characters from Rick and Morty created by Justin Roiland and Dan Harmon
- Built using Hugging Face Transformers and PyTorch
- UI inspired by "The Matrix" franchise

---

*"Wubba lubba dub dub!" - Rick Sanchez*