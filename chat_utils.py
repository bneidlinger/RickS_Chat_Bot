import random
import torch
from rick_processor import rickify_response
from rick_config import CONFIG, RICK_CHARACTER_CONTEXT, FALLBACK_RESPONSES

def get_ai_response(user_input, model, tokenizer, conversation_history, session_id="default", device="cpu"):
    """
    Generate an AI response using the provided model and tokenizer,
    then transform it to sound like Rick Sanchez.
    """
    # Initialize conversation history for this session if it doesn't exist
    if session_id not in conversation_history:
        conversation_history[session_id] = []

    # Add the new user input to the history
    max_turns = CONFIG["conversation"]["max_turns"]
    if len(conversation_history[session_id]) >= max_turns:
        conversation_history[session_id].pop(0)
    conversation_history[session_id].append(user_input)
    
    # Create a full conversation context
    full_context = ""
    
    # Add Rick-specific context to guide the model
    if CONFIG["conversation"]["use_rick_context"]:
        full_context += RICK_CHARACTER_CONTEXT + "\n\n"
    
    # Add previous conversation turns if available (up to 3 turns)
    history_snippet = conversation_history[session_id][-3:] if len(conversation_history[session_id]) > 1 else []
    if history_snippet:
        full_context += "Previous conversation:\n"
        for prev_msg in history_snippet:
            full_context += f"- {prev_msg}\n"
    
    # Add the current question
    full_context += f"\nCurrent question: {user_input}\n\nRick's response:"
    
    try:
        # Detect question type for adaptive response generation
        if CONFIG["conversation"]["use_adaptive_generation"]:
            generation_params = get_adaptive_parameters(user_input)
        else:
            generation_params = CONFIG["model"]["default_params"]
        
        # Format input for model with the constructed context
        inputs = tokenizer(full_context, 
                          return_tensors="pt", 
                          max_length=512, 
                          truncation=True).to(device)

        # Generate response
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                **generation_params
            )

        # Decode the generated response
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract just the response part if it includes the prompt
        if "Rick's response:" in response:
            response = response.split("Rick's response:")[1].strip()
        
        # Apply additional preprocessing to improve responses before Rickification
        response = improve_response_quality(response, user_input)
        
        # Rickify the response with configured intensity
        response = rickify_response(response)

        # Clear CUDA cache if using GPU
        if device == "cuda":
            torch.cuda.empty_cache()

        return response
    except Exception as e:
        print(f"Error in model inference: {e}")
        return rickify_response(random.choice(FALLBACK_RESPONSES))

def get_adaptive_parameters(user_input):
    """
    Adjust generation parameters based on question type for better responses
    """
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
    if CONFIG["enhancement"]["clean_generic_phrases"]:
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
    if CONFIG["enhancement"]["add_science_terms"]:
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
                        response = response[:sentence_end] + f". It's basic {term} physics, really." + response[sentence_end+1:]
    
    # Clean up response
    response = response.strip()
    
    # Ensure we have something to return
    if not response or len(response.split()) < 3:
        response = "Look, I'm too busy for this. Ask something that requires my genius brain."
        
    return response