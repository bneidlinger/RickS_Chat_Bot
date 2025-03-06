import random
import re

# Rick's catchphrases and speech patterns
RICK_CATCHPHRASES = [
    "Wubba lubba dub dub!",
    "And that's the waaaay the news goes!",
    "Grass... tastes bad!",
    "Lick, lick, lick my balls!",
    "Uh oh, somersault jump!",
    "Hit the sack, Jack!",
    "Rikki-tikki-tavi, biatch!",
    "And that's why I always say, shum-shum-schlippity-dop!",
    "AIDS!",
    "That's the way I like it, baby!",
    "Burger time!",
    "No jumping in the sewer!",
    "BURP!",
    "*BURRRP*",
    "I'm pickle Riiiick!"
]

RICK_INTERJECTIONS = [
    "Morty",
    "Listen Morty",
    "Look",
    "Listen",
    "Oh geez",
    "Uhhh",
    "I mean",
    "W-w-w-what do you expect",
    "In this dimension",
    "Scientifically speaking",
    "*burp*",
    "Mathematically speaking",
    "Sweet Jesus",
    "Holy crap",
    "Big deal",
    "Get a load of this",
    "I-I-I gotta tell ya",
    "W-w-w-what are you, stupid?"
]

RICK_ENDINGS = [
    "That's just how it is in this crazy multiverse.",
    "And don't even get me started on the implications.",
    "That's just slavery with extra steps.",
    "I've seen better in dimension C-137.",
    "Boom! Big reveal!",
    "And that's science for ya.",
    "You know what I'm talking about?",
    "Your mind blown yet?",
    "Waaaaay up your butt.",
    "Peace among worlds.",
    "You're welcome.",
    "That's just how grandpa rolls.",
    "I do this every day, no big deal."
]

RICK_REPLACEMENTS = {
    "I think": "I-I-I'm pretty sure",
    "I believe": "Listen up, cause",
    "maybe": "probably, in most dimensions",
    "could be": "is definitely, except in dimension C-500",
    "I don't know": "even my genius brain isn't sure",
    "exactly": "precisely, you moron",
    "certainly": "100% certain, and I'm never wrong",
    "yes": "y-y-yeah, obviously",
    "no": "hell no",
    "hello": "what's up",
    "hi": "hey there, *burp*",
    "goodbye": "see ya later, wouldn't wanna be ya",
    "impressive": "not bad for a non-genius",
    "surprising": "holy crap, that's actually",
    "interesting": "mildly intriguing to my genius brain",
}

# Rick's mood factors
RICK_MOODS = {
    "frustrated": {
        "interjections": ["Jesus christ", "For fuck's sake", "Are you kidding me", "Oh, great", "Christ"],
        "catchphrases": ["You're killing me!", "I'm surrounded by idiots!", "I need a drink."],
        "stutter_probability": 0.4,
        "burp_probability": 0.3,
        "endings": ["Just... wow.", "I can't with this right now.", "This is way beneath me."]
    },
    "excited": {
        "interjections": ["Holy shit", "Oh my god", "Sweet mother of", "Check this out"],
        "catchphrases": ["This is gonna be good!", "Now we're talking!", "Time to get schwifty!"],
        "stutter_probability": 0.6,  # More stuttering when excited
        "burp_probability": 0.5,
        "endings": ["This is gonna change everything!", "Science, bitch!", "Mind = blown!"]
    },
    "dismissive": {
        "interjections": ["Whatever", "Pfft", "Yeah yeah", "Sure", "Right"],
        "catchphrases": ["Been there, done that.", "Snooze fest.", "Next!"],
        "stutter_probability": 0.2,  # Less stuttering when dismissive
        "burp_probability": 0.4,
        "endings": ["Boring.", "Next question.", "Let's move on to something that matters."]
    },
    "drunk": {
        "interjections": ["Heyyy", "Whooooo", "Listen listen listen", "*hiccup*"],
        "catchphrases": ["I'm so *burp* wasted.", "Pass me the flask, Morty!", "Drunk science is best science!"],
        "stutter_probability": 0.7,  # More stuttering when drunk
        "burp_probability": 0.7,
        "endings": ["I need another drink.", "*passes out*", "Where's my flask?"]
    }
}

# Rick's scientific terminology
RICK_SCIENCE_TERMS = {
    "physics": ["quantum", "interdimensional", "relativity", "subatomic", "temporal", "particle", "wave function"],
    "biology": ["DNA", "neutrino", "biomass", "cellular", "synaptic", "RNA", "genetic"],
    "chemistry": ["molecular", "atomic", "chemical", "isotope", "compound", "element", "reaction"],
    "dimensions": ["C-137", "J19ζ7", "alternate timeline", "parallel universe", "fifth dimension", "microverse", "miniverse"]
}

# Track usage of catchphrases to avoid repetition
used_catchphrases = []
used_interjections = []
used_endings = []

def determine_rick_mood(text):
    """Determine Rick's mood based on the content of the response"""
    text_lower = text.lower()
    
    # Check for question patterns that might frustrate Rick
    if "?" in text or any(word in text_lower for word in ["why", "how come", "explain"]):
        if any(word in text_lower for word in ["basic", "simple", "obvious", "everyone knows"]):
            return "frustrated"
    
    # Check for scientific/discovery patterns that might excite Rick
    if any(word in text_lower for word in ["discover", "invent", "breakthrough", "amazing", "incredible"]):
        return "excited"
    
    # Check for mundane topics that Rick might dismiss
    if any(word in text_lower for word in ["normal", "everyday", "regular", "human", "feelings", "emotions"]):
        return "dismissive"
    
    # Check for alcohol references or signs of intoxication
    if any(word in text_lower for word in ["drink", "alcohol", "beer", "whiskey", "flask", "drunk", "wasted"]):
        return "drunk"
    
    # Default to random mood with weighted probabilities
    moods = ["frustrated", "excited", "dismissive", "drunk"]
    weights = [0.3, 0.3, 0.3, 0.1]  # Less likely to be drunk by default
    return random.choices(moods, weights=weights)[0]

def get_unused_item(items_list, used_items):
    """Get an item that hasn't been used recently"""
    available_items = [item for item in items_list if item not in used_items]
    if not available_items:
        # If all items have been used, reset and use any
        used_items.clear()
        available_items = items_list
    
    chosen_item = random.choice(available_items)
    used_items.append(chosen_item)
    
    # Keep the used list reasonable in size
    if len(used_items) > len(items_list) // 2:
        used_items.pop(0)
    
    return chosen_item

def insert_science_references(text):
    """Insert scientific terminology into the text"""
    if random.random() < 0.4:
        category = random.choice(list(RICK_SCIENCE_TERMS.keys()))
        term = random.choice(RICK_SCIENCE_TERMS[category])
        
        # Find a good spot to insert the term
        sentences = re.split(r'(?<=[.!?])\s+', text)
        if len(sentences) > 1:
            insert_idx = random.randint(0, len(sentences) - 1)
            
            # Create a science reference
            if random.random() < 0.5:
                science_ref = f" It's like {term} theory 101."
            else:
                science_ref = f" Any idiot with basic {term} knowledge would know that."
            
            # Insert the reference
            sentences[insert_idx] = sentences[insert_idx].rstrip('.!?') + science_ref
            text = ' '.join(sentences)
    
    return text

def rickify_response(response):
    """Transform a normal AI response to sound like Rick from Rick and Morty with mood awareness"""
    
    # Determine Rick's mood for this response
    mood = determine_rick_mood(response)
    mood_config = RICK_MOODS[mood]
    
    # Start with a burp or interjection sometimes
    if random.random() < 0.5:
        if random.random() < 0.3 and mood_config["interjections"]:
            # Use mood-specific interjection
            interjection = random.choice(mood_config["interjections"])
        else:
            # Use general interjection
            interjection = get_unused_item(RICK_INTERJECTIONS, used_interjections)
        
        response = f"{interjection}, {response.lower()}"
    
    # Replace certain phrases with Rick-like alternatives
    for normal, rick in RICK_REPLACEMENTS.items():
        # Use word boundaries to only replace whole words, case-insensitive
        response = re.sub(r'\b' + normal + r'\b', rick, response, flags=re.IGNORECASE)
    
    # Stutter on some words that start with certain letters
    words = response.split()
    for i, word in enumerate(words):
        if len(word) > 2 and word[0].lower() in "abcdefgw" and random.random() < mood_config["stutter_probability"]:
            # Add stuttering like "w-w-word"
            words[i] = f"{word[0]}-{word[0]}-{word}"
    response = " ".join(words)
    
    # Add random stuttering on "I"
    response = re.sub(r'\bI\b', lambda x: "I-I-I" if random.random() < mood_config["stutter_probability"] else "I", response)
    
    # Add a catchphrase at the beginning or end sometimes
    if random.random() < 0.25:
        if random.random() < 0.4 and mood_config["catchphrases"]:
            # Use mood-specific catchphrase
            catchphrase = random.choice(mood_config["catchphrases"])
        else:
            # Use general catchphrase
            catchphrase = get_unused_item(RICK_CATCHPHRASES, used_catchphrases)
        
        if random.random() < 0.7:
            response = f"{catchphrase} {response}"
        else:
            response = f"{response} {catchphrase}"
    
    # Add a Rick-like ending sometimes
    if random.random() < 0.3 and not response.endswith((".", "!", "?")):
        response += "."
    if random.random() < 0.35:
        if random.random() < 0.4 and mood_config["endings"]:
            # Use mood-specific ending
            ending = random.choice(mood_config["endings"])
        else:
            # Use general ending
            ending = get_unused_item(RICK_ENDINGS, used_endings)
        
        response += f" {ending}"
    
    # Add some random burps
    if random.random() < mood_config["burp_probability"]:
        sentences = re.split(r'(?<=[.!?])\s+', response)
        for i in range(len(sentences)):
            if random.random() < 0.3:
                words = sentences[i].split()
                if words:
                    burp_idx = random.randint(0, len(words) - 1)
                    words[burp_idx] = words[burp_idx] + " *burp*"
                    sentences[i] = " ".join(words)
        response = ' '.join(sentences)
    
    # Insert some scientific terminology
    response = insert_science_references(response)
    
    # Add dimension references sometimes
    if random.random() < 0.2:
        dimension_refs = [
            f" Not in this dimension, anyway.",
            f" Maybe in dimension {random.choice(['C-137', 'J19ζ7', 'D-99', 'C-500', '35-C'])}, but not here.",
            f" The Council of Ricks would agree with me.",
            f" Even the Citadel doesn't understand this stuff.",
            f" I've got a portal gun that could solve this in seconds.",
            f" My portal gun technology proves it.",
            f" I could build a device to fix this with some scraps and a good buzz going."
        ]
        response += random.choice(dimension_refs)
    
    return response