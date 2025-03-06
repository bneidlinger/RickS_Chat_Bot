import os
import torch
from flask import Flask, request, jsonify, render_template, session
from flask_socketio import SocketIO, emit
import eventlet
import random
import secrets
import traceback
from werkzeug.middleware.proxy_fix import ProxyFix

# Create the necessary directory structure
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "model")
os.makedirs(MODEL_DIR, exist_ok=True)

app = Flask(__name__, template_folder="templates", static_folder="static")
app.config['SECRET_KEY'] = secrets.token_hex(16)  # Secure secret key
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)  # For proper IP handling behind proxies

socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Set device
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {device}")

# Global variables for model and tokenizer
model = None
tokenizer = None

# Import rick modules (these will be created in separate files)
try:
    print("Attempting to import Rick modules...")
    from rick_processor import rickify_response

    print("Successfully imported rick_processor")

    from rick_config import CONFIG, RICK_CHARACTER_CONTEXT, FALLBACK_RESPONSES

    print("Successfully imported rick_config")

    print("Rick modules loaded successfully!")
    RICK_MODULES_LOADED = True
except ImportError as e:
    print(f"Error importing Rick modules: {e}")
    print(f"Current directory: {os.getcwd()}")
    print(f"Files in directory: {os.listdir('.')}")
    print("Using basic rickification.")
    RICK_MODULES_LOADED = False


    # Basic fallback rickify function if modules aren't available
    def rickify_response(text):
        burps = ["*burp*", "*BURP*", "BURRP", "*hic*"]
        prefixes = ["Listen, ", "Look, ", "Morty, ", ""]

        if random.random() < 0.3:
            text = f"{random.choice(burps)} {text}"
        if random.random() < 0.4:
            text = f"{random.choice(prefixes)}{text}"
        if random.random() < 0.2:
            text = text.replace("I ", "I-I-I ")

        return text


def download_model():
    """
    Download a better model for offline chat.
    Options:
    - "facebook/blenderbot-400M-distill" (good balance of quality and size)
    - "facebook/blenderbot-1B-distill" (better but larger)
    - "microsoft/DialoGPT-medium" (if you want to stay with DialoGPT family)
    - "meta-llama/Llama-2-7b-chat-hf" (with Hugging Face access token)
    """
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer, BlenderbotTokenizer

    global model, tokenizer

    # Get model name from config if available, otherwise use default
    if RICK_MODULES_LOADED:
        MODEL_NAME = CONFIG["model"]["name"]
    else:
        MODEL_NAME = "facebook/blenderbot-1B-distill"

    print(f"Downloading model {MODEL_NAME} to {MODEL_DIR}...")

    # Download and save tokenizer
    tokenizer = BlenderbotTokenizer.from_pretrained(MODEL_NAME)
    tokenizer.save_pretrained(MODEL_DIR)
    print("Tokenizer saved successfully!")

    # Download and save model
    model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)
    model.save_pretrained(MODEL_DIR)
    print("Model saved successfully!")


def load_local_model():
    """
    Load the model from local directory.
    """
    from transformers import AutoModelForSeq2SeqLM, BlenderbotTokenizer

    global model, tokenizer

    print(f"Loading model from {MODEL_DIR}...")

    # Load tokenizer and model matching the model type
    tokenizer = BlenderbotTokenizer.from_pretrained(MODEL_DIR)
    model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_DIR)
    model.to(device)

    print("Model loaded successfully!")


# Check if model exists, download if not
if not os.path.exists(os.path.join(MODEL_DIR, "pytorch_model.bin")):
    try:
        download_model()
    except Exception as e:
        print(f"Error downloading model: {e}")
        print("Please ensure you have internet connection for the first run or download the model manually.")
        import sys

        sys.exit(1)
else:
    load_local_model()

# Store conversation history as a dict of sessions
conversation_history = {}


# Function to create improved responses with context awareness
def get_adaptive_parameters(user_input):
    """
    Adjust generation parameters based on question type for better responses
    """
    if not RICK_MODULES_LOADED:
        # Default parameters if rick_config is not available
        return {
            "max_length": 150,
            "min_length": 20,
            "temperature": 0.85,
            "top_p": 0.92,
            "num_beams": 4,
            "repetition_penalty": 1.2,
            "no_repeat_ngram_size": 2
        }

    user_input = user_input.lower()

    # Detect question types
    is_scientific = any(word in user_input for word in
                        ['science', 'physics', 'dimension', 'universe', 'theory', 'quantum',
                         'technology', 'portal', 'invention', 'experiment'])

    is_personal = any(word in user_input for word in
                      ['you', 'your', 'feel', 'think', 'opinion', 'morty', 'family',
                       'beth', 'jerry', 'summer', 'citadel', 'council', 'enemy'])

    is_philosophical = any(word in user_input for word in
                           ['meaning', 'life', 'purpose', 'existence', 'universe', 'god',
                            'reality', 'consciousness', 'soul', 'morality'])

    # Get base parameters
    params = CONFIG["model"]["default_params"].copy()

    # Adjust parameters based on question type
    if is_scientific:
        # More coherent and detailed for scientific topics
        params.update({
            "max_length": 200,
            "min_length": 50,
            "temperature": 0.7,
            "top_p": 0.92,
            "num_beams": 5,
            "repetition_penalty": 1.2,
            "length_penalty": 1.0
        })
    elif is_personal:
        # More creative and erratic for personal questions
        params.update({
            "max_length": 150,
            "min_length": 30,
            "temperature": 0.9,
            "top_p": 0.95,
            "num_beams": 3,
            "repetition_penalty": 1.3,
            "length_penalty": 0.8
        })
    elif is_philosophical:
        # More nihilistic and weird for philosophical questions
        params.update({
            "max_length": 175,
            "min_length": 40,
            "temperature": 0.85,
            "top_p": 0.97,
            "num_beams": 3,
            "repetition_penalty": 1.1,
            "length_penalty": 1.2
        })

    return params


def improve_response_quality(response, user_input):
    """Apply additional preprocessing to improve response quality"""

    # Skip processing if response is too short
    if not response or len(response) < 5:
        return "Look, I'm too busy for this. Ask something that requires my genius brain."

    # Remove generic/templated phrases that don't sound like Rick
    generic_phrases = [
        "I'm here to help",
        "I'd be happy to",
        "As an AI",
        "I don't have personal",
        "I cannot",
        "I don't have the ability",
        "As a language model"
    ]

    for phrase in generic_phrases:
        if phrase in response:
            response = response.replace(phrase, "")

    # Add science references for science questions
    if any(word in user_input.lower() for word in ['how', 'why', 'what', 'explain']):
        if not any(term in response.lower() for term in ['dimension', 'science', 'quantum', 'portal']):
            science_terms = [
                "interdimensional",
                "quantum",
                "multiverse",
                "temporal",
                "subatomic",
                "molecular",
                "neural",
                "galactic"
            ]
            if len(response) > 0:
                term = random.choice(science_terms)
                sentence_end = response.find('.')
                if sentence_end > 0:
                    response = response[:sentence_end] + f". It's basic {term} physics, really." + response[
                                                                                                   sentence_end + 1:]

    # Clean up response
    response = response.strip()

    # Ensure we have something to return
    if not response or len(response.split()) < 3:
        return "Look, I'm too busy for this. Ask something that requires my genius brain."

    return response


# The main AI response generation function
# Update this part of the get_ai_response function to handle the context length properly:

def get_ai_response(user_input, session_id="default"):
    """Generate an AI response that sounds like Rick from Rick and Morty"""

    # Debug info
    print(f"Processing input: '{user_input}' for session '{session_id}'")

    # Initialize conversation history for this session if it doesn't exist
    if session_id not in conversation_history:
        conversation_history[session_id] = []
        print(f"Created new conversation history for session '{session_id}'")

    # Get max_turns from config if available, otherwise use default
    max_turns = CONFIG["conversation"]["max_turns"] if RICK_MODULES_LOADED else 5

    # Add the new user input to the history
    if len(conversation_history[session_id]) >= max_turns:
        conversation_history[session_id].pop(0)
    conversation_history[session_id].append(user_input)

    # Use direct rickification for very short inputs to avoid model issues
    if len(user_input.split()) <= 3 and not any(word in user_input.lower() for word in
                                                ['why', 'how', 'what', 'when', 'where', 'explain']):
        simple_responses = [
            "Yeah, whatever.",
            "Is that all you've got to say?",
            "Fascinating conversation skills you got there.",
            "Oh great, another genius with vocabulary issues.",
            "Keep it coming, Einstein.",
            "That's your brilliant contribution?",
            "Wow, profound stuff right there.",
            "I'm blown away by your eloquence.",
        ]
        response = random.choice(simple_responses)
        return rickify_response(response)

    try:
        # First try with minimal context to avoid embedding size issues
        try:
            # Just use a simple prompt with the question
            simple_context = f"As Rick Sanchez from Rick and Morty, respond to: {user_input}"

            print(f"Trying simple context approach: {simple_context}")

            # Format input for model
            inputs = tokenizer(simple_context,
                               return_tensors="pt",
                               max_length=128,  # Limit context length
                               truncation=True).to(device)

            # Simple default parameters
            params = {
                "max_length": 100,
                "min_length": 20,
                "do_sample": True,  # Enable sampling
                "temperature": 0.9,
                "top_p": 0.92,
                "num_beams": 4,
                "repetition_penalty": 1.2,
                "no_repeat_ngram_size": 2,
            }

            # Generate response
            print("Generating response with simple context...")
            with torch.no_grad():
                outputs = model.generate(
                    **inputs,
                    **params
                )

            # Decode the generated response
            response = tokenizer.decode(outputs[0], skip_special_tokens=True)
            print(f"Generated response: {response[:100]}...")

        except Exception as e:
            print(f"Simple context approach failed: {str(e)}")

            # Fall back to predetermined responses for different question types
            print("Falling back to themed responses...")

            # Categorize the question
            question_lower = user_input.lower()

            if any(word in question_lower for word in ['universe', 'dimension', 'portal', 'space', 'time']):
                themed_responses = [
                    "The multiverse is infinitely complex. Your human brain couldn't comprehend it.",
                    "Dimensions are like TV channels, except every channel has a different version of you that's slightly less pathetic.",
                    "Time and space are just constructs. I've been to places where time runs backwards and pizza eats people.",
                    "My portal gun lets me travel anywhere in the multiverse. It's powered by crystallized quantum energy, something you'll never understand.",
                ]
                response = random.choice(themed_responses)

            elif any(word in question_lower for word in ['science', 'physics', 'chemistry', 'biology', 'math']):
                themed_responses = [
                    "Science isn't about asking stupid questions, it's about questioning stupid answers.",
                    "Your understanding of physics is like a toddler trying to understand calculus.",
                    "I've synthesized chemicals that would make your brain explode just by looking at them.",
                    "Math is the universal language. Too bad you're speaking baby talk.",
                ]
                response = random.choice(themed_responses)

            elif any(word in question_lower for word in ['morty', 'family', 'beth', 'summer', 'jerry']):
                themed_responses = [
                    "Morty's a good kid, but sometimes his stupidity makes me want to move to another dimension.",
                    "My family? They're the reason I drink. Well, one of the reasons.",
                    "Beth's my daughter. She's almost as smart as me, but wasted her potential cutting up horses.",
                    "Jerry is the human equivalent of a participation trophy.",
                    "Summer's alright. At least she doesn't follow me around like a lost puppy like Morty.",
                ]
                response = random.choice(themed_responses)

            else:
                themed_responses = [
                    "I've seen things that would make your brain melt.",
                    "That's the kind of question that gets people killed in dimension C-137.",
                    "I could explain it to you, but you'd need at least 15 more IQ points to understand.",
                    "I don't have time for this. I've got experiments running in the garage.",
                    "In an infinite multiverse, there's a version of me that cares about this question. I'm not that version.",
                ]
                response = random.choice(themed_responses)

        # Improve the response quality
        response = improve_response_quality(response, user_input)

        # Rickify the response
        print("Rickifying response...")
        response = rickify_response(response)
        print(f"Final response: {response[:100]}...")

        # Clear CUDA cache if using GPU
        if device == "cuda":
            torch.cuda.empty_cache()

        return response
    except Exception as e:
        print(f"Error in model inference: {str(e)}")
        print(traceback.format_exc())  # Print full stack trace
        if RICK_MODULES_LOADED:
            fallback = random.choice(FALLBACK_RESPONSES)
            print(f"Using fallback response: {fallback}")
            return rickify_response(fallback)
        else:
            fallback = "I'm having trouble processing that. Could we try a different conversation?"
            print(f"Using basic fallback response: {fallback}")
            return rickify_response(fallback)


@app.route("/")
def index():
    return render_template("chat.html")


@app.route("/chat", methods=["POST"])
def chat():
    user_input = request.json.get("message")
    session_id = request.json.get("session_id", "default")

    if not user_input:
        return jsonify({"error": "No message provided"}), 400

    ai_response = get_ai_response(user_input, session_id)
    return jsonify({"response": ai_response})


@socketio.on("message")
def handle_message(data):
    # Check if data is a string or a dictionary
    if isinstance(data, str):
        message = data
        session_id = "default"
    else:
        message = data.get("message", "")
        session_id = data.get("session_id", "default")

    print(f"Received socket message: '{message}' for session '{session_id}'")

    emit("response", {"type": "typing"}, broadcast=False)

    # Add a random delay to make it seem more natural
    typing_delay = len(message) * 0.03  # ~30ms per character
    typing_delay = min(max(typing_delay, 0.5), 2.5)  # Between 0.5 and 2.5 seconds
    print(f"Waiting {typing_delay} seconds for typing effect...")
    eventlet.sleep(typing_delay)

    # Generate response
    try:
        ai_response = get_ai_response(message, session_id)
        print(f"Sending response: '{ai_response[:100]}...'")
    except Exception as e:
        print(f"Error generating response: {str(e)}")
        print(traceback.format_exc())
        ai_response = rickify_response("I'm having trouble processing that right now. Could you try again?")

    emit("response", {"type": "message", "text": ai_response})


@app.route("/clear_history", methods=["POST"])
def clear_history():
    session_id = request.json.get("session_id", "default")
    print(f"Clearing history for session '{session_id}'")
    if session_id in conversation_history:
        conversation_history[session_id] = []
    return jsonify({"status": "success"})


@app.errorhandler(404)
def page_not_found(e):
    return render_template("error.html", error="404 - Page Not Found"), 404


@app.errorhandler(500)
def server_error(e):
    return render_template("error.html", error="500 - Internal Server Error"), 500


if __name__ == "__main__":
    print(f"Starting server with Rick modules {'loaded' if RICK_MODULES_LOADED else 'not loaded'}")
    socketio.run(app, debug=True, host="0.0.0.0", port=5000)