 
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import re
import ast
import math
import random
import difflib
from datetime import datetime

app = Flask(__name__)
CORS(app)

# =====================================================================
# CONVERSATION MEMORY (per session, in-memory only — no external calls)
# =====================================================================
sessions = {}

def get_session(sid):
    if sid not in sessions:
        sessions[sid] = {"history": [], "last_joke": -1, "last_fact": -1}
    return sessions[sid]


# =====================================================================
# SAFE MATH ENGINE (no eval() — uses an AST whitelist, so it can't
# execute arbitrary code the way the original eval()-based version could)
# =====================================================================
ALLOWED_BINOPS = {
    ast.Add: lambda a, b: a + b,
    ast.Sub: lambda a, b: a - b,
    ast.Mult: lambda a, b: a * b,
    ast.Div: lambda a, b: a / b,
    ast.Pow: lambda a, b: a ** b,
    ast.Mod: lambda a, b: a % b,
    ast.FloorDiv: lambda a, b: a // b,
}
ALLOWED_UNARY = {
    ast.USub: lambda a: -a,
    ast.UAdd: lambda a: a,
}
ALLOWED_FUNCS = {
    "sqrt": math.sqrt, "sin": math.sin, "cos": math.cos, "tan": math.tan,
    "log": math.log, "log10": math.log10, "exp": math.exp,
    "floor": math.floor, "ceil": math.ceil, "abs": abs, "round": round,
    "factorial": math.factorial,
}
ALLOWED_NAMES = {"pi": math.pi, "e": math.e}

class MathError(Exception):
    pass

def _eval_node(node):
    if isinstance(node, ast.Expression):
        return _eval_node(node.body)
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise MathError("bad constant")
    if isinstance(node, ast.BinOp) and type(node.op) in ALLOWED_BINOPS:
        return ALLOWED_BINOPS[type(node.op)](_eval_node(node.left), _eval_node(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in ALLOWED_UNARY:
        return ALLOWED_UNARY[type(node.op)](_eval_node(node.operand))
    if isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name) and node.func.id in ALLOWED_FUNCS:
            args = [_eval_node(a) for a in node.args]
            return ALLOWED_FUNCS[node.func.id](*args)
        raise MathError("bad function")
    if isinstance(node, ast.Name) and node.id in ALLOWED_NAMES:
        return ALLOWED_NAMES[node.id]
    raise MathError("disallowed expression")

def safe_eval(expr):
    tree = ast.parse(expr, mode="eval")
    return _eval_node(tree)

def normalize_math_words(text):
    t = " " + text.lower() + " "
    t = re.sub(r"\bplus\b", "+", t)
    t = re.sub(r"\bminus\b", "-", t)
    t = re.sub(r"\b(multiplied by|times)\b", "*", t)
    t = re.sub(r"\bdivided by\b", "/", t)
    t = re.sub(r"\bto the power of\b", "**", t)
    t = re.sub(r"\bsquared\b", "**2", t)
    t = re.sub(r"\bcubed\b", "**3", t)
    return t

def math_engine(text):
    t = text.lower().strip()

    # "X percent of Y"
    m = re.search(r"(-?\d+\.?\d*)\s*(?:%|percent)\s*of\s*(-?\d+\.?\d*)", t)
    if m:
        a, b = float(m.group(1)), float(m.group(2))
        result = (a / 100) * b
        return f"{a}% of {b} is {round(result, 6)}"

    # "square root of X"
    m = re.search(r"square root of (-?\d+\.?\d*)", t)
    if m:
        try:
            return f"The square root of {m.group(1)} is {round(math.sqrt(float(m.group(1))), 6)}"
        except ValueError:
            return "That number doesn't have a real square root."

    # natural-language math
    normalized = normalize_math_words(t)
    candidate = re.sub(r"[^0-9+\-*/().%\s]", " ", normalized)
    candidate = candidate.strip()

    if not candidate or not any(op in candidate for op in "+-*/^"):
        return None
    if not any(ch.isdigit() for ch in candidate):
        return None
    if not re.fullmatch(r"[0-9+\-*/().\s]+", candidate):
        return None

    try:
        result = safe_eval(candidate)
        if isinstance(result, float) and result.is_integer():
            result = int(result)
        return f"The result is {result}"
    except (MathError, ZeroDivisionError, SyntaxError, ValueError, TypeError, OverflowError):
        return None


# =====================================================================
# UNIT CONVERSION ENGINE
# =====================================================================
UNIT_ALIASES = {
    "km": "km", "kilometer": "km", "kilometers": "km",
    "mi": "mi", "mile": "mi", "miles": "mi",
    "kg": "kg", "kilogram": "kg", "kilograms": "kg",
    "lb": "lb", "lbs": "lb", "pound": "lb", "pounds": "lb",
    "c": "c", "celsius": "c",
    "f": "f", "fahrenheit": "f",
    "m": "m", "meter": "m", "meters": "m", "metre": "m", "metres": "m",
    "ft": "ft", "feet": "ft", "foot": "ft",
    "cm": "cm", "centimeter": "cm", "centimeters": "cm",
    "in": "in", "inch": "in", "inches": "in",
    "l": "l", "liter": "l", "liters": "l", "litre": "l", "litres": "l",
    "gal": "gal", "gallon": "gal", "gallons": "gal",
}

CONVERSIONS = {
    ("km", "mi"): lambda x: x * 0.621371,
    ("mi", "km"): lambda x: x / 0.621371,
    ("kg", "lb"): lambda x: x * 2.20462,
    ("lb", "kg"): lambda x: x / 2.20462,
    ("c", "f"): lambda x: x * 9 / 5 + 32,
    ("f", "c"): lambda x: (x - 32) * 5 / 9,
    ("m", "ft"): lambda x: x * 3.28084,
    ("ft", "m"): lambda x: x / 3.28084,
    ("cm", "in"): lambda x: x / 2.54,
    ("in", "cm"): lambda x: x * 2.54,
    ("l", "gal"): lambda x: x * 0.264172,
    ("gal", "l"): lambda x: x / 0.264172,
}

def unit_engine(text):
    t = text.lower()
    unit_words = "|".join(sorted(UNIT_ALIASES.keys(), key=len, reverse=True))
    pattern = rf"(-?\d+\.?\d*)\s*({unit_words})s?\s*(?:to|in|->)\s*({unit_words})s?"
    m = re.search(pattern, t)
    if not m:
        return None
    val, from_u, to_u = float(m.group(1)), UNIT_ALIASES.get(m.group(2)), UNIT_ALIASES.get(m.group(3))
    if not from_u or not to_u:
        return None
    if from_u == to_u:
        return f"{val} {from_u} is already {val} {to_u}."
    fn = CONVERSIONS.get((from_u, to_u))
    if not fn:
        return None
    result = round(fn(val), 4)
    return f"{val} {from_u} ≈ {result} {to_u}"


# =====================================================================
# TIME / DATE ENGINE
# =====================================================================
def time_engine(text):
    t = text.lower()
    now = datetime.now()
    if re.search(r"\bwhat time\b|\bcurrent time\b", t):
        return f"The server's local time is {now.strftime('%I:%M %p')}."
    if re.search(r"\bwhat.?s the date\b|\btoday.?s date\b|\bwhat day\b", t):
        return f"Today is {now.strftime('%A, %B %d, %Y')}."
    return None


# =====================================================================
# GREETINGS / SMALL TALK
# =====================================================================
GREETING_TRIGGERS = {
    "hi": ["Hey! What's up?", "Hi there!", "Hello!"],
    "hello": ["Hello! How can I help?", "Hi!"],
    "hey": ["Hey there!", "Hey! What can I do for you?"],
    "yo": ["Yo!"],
    "sup": ["Not much! What's up with you?"],
    "goodmorning": ["Good morning! ☀️"],
    "goodnight": ["Good night! 🌙"],
}
FAREWELL_TRIGGERS = ["bye", "goodbye", "seeya", "see ya", "later", "cya"]
THANKS_TRIGGERS = ["thank you", "thanks", "thx", "ty"]
HOWAREYOU_TRIGGERS = ["how are you", "how're you", "how you doing"]

def _has_phrase(t, phrase):
    return re.search(rf"\b{re.escape(phrase)}\b", t) is not None

def smalltalk_engine(text):
    t = re.sub(r"[^a-z ]", "", text.lower()).strip()
    compact = t.replace(" ", "")

    if any(_has_phrase(t, p) for p in THANKS_TRIGGERS):
        return random.choice(["You're welcome!", "Anytime!", "Happy to help!"])
    if any(_has_phrase(t, p) for p in HOWAREYOU_TRIGGERS):
        return random.choice(["Doing great, thanks for asking! How about you?", "All good here! What's on your mind?"])
    if any(p == t or p in t.split() for p in FAREWELL_TRIGGERS):
        return random.choice(["See ya!", "Goodbye!", "Later!"])
    for key, responses in GREETING_TRIGGERS.items():
        if key == compact or key in t.split():
            return random.choice(responses)
    if t in ("help", "what can you do"):
        return ("I can help with: math (arithmetic, percentages, square roots), unit "
                "conversions (km↔mi, kg↔lb, C↔F, etc.), the current time/date, and "
                "quick facts across science, geography, history, and more. Try asking "
                "me something, or say 'tell me a fact' or 'tell me a joke'!")
    return None


# =====================================================================
# JOKES & FUN FACTS
# =====================================================================
JOKES = [
    "Why don't scientists trust atoms? Because they make up everything!",
    "I told my computer I needed a break, and it said 'no problem — I'll go to sleep.'",
    "Why did the math book look sad? It had too many problems.",
    "Parallel lines have so much in common. It's a shame they'll never meet.",
    "What do you call a fish with no eyes? A fsh.",
    "I would tell you a UDP joke, but you might not get it.",
]

FUN_FACTS = [
    "Honey never spoils — archaeologists have found 3,000-year-old honey in Egyptian tombs that's still edible.",
    "Octopuses have three hearts and blue blood.",
    "A group of flamingos is called a 'flamboyance'.",
    "Bananas are berries, but strawberries aren't.",
    "The Eiffel Tower can grow taller in summer due to thermal expansion of the metal.",
    "A day on Venus is longer than a year on Venus.",
    "Wombat poop is cube-shaped.",
]

def fun_engine(text, sess):
    t = text.lower()
    if "joke" in t:
        idx = random.randrange(len(JOKES))
        while len(JOKES) > 1 and idx == sess["last_joke"]:
            idx = random.randrange(len(JOKES))
        sess["last_joke"] = idx
        return JOKES[idx]
    if "fun fact" in t or "random fact" in t or "tell me a fact" in t:
        idx = random.randrange(len(FUN_FACTS))
        while len(FUN_FACTS) > 1 and idx == sess["last_fact"]:
            idx = random.randrange(len(FUN_FACTS))
        sess["last_fact"] = idx
        return FUN_FACTS[idx]
    return None


# =====================================================================
# KNOWLEDGE BASE
# =====================================================================
KNOWLEDGE = {
    # Physics
    "proton": "A proton is a positively charged particle found in the nucleus of an atom.",
    "neutron": "A neutron is a neutral (uncharged) particle found in the nucleus of an atom.",
    "electron": "An electron is a negatively charged particle that orbits an atom's nucleus.",
    "gravity": "Gravity is the force that attracts objects with mass toward each other.",
    "momentum": "Momentum is a measure of motion, calculated as mass multiplied by velocity.",
    "force": "A force is any push or pull that can change an object's motion.",
    "energy": "Energy is the capacity to do work or cause change; it comes in many forms like kinetic, potential, and thermal.",
    "friction": "Friction is a force that resists motion between two surfaces in contact.",
    "velocity": "Velocity is speed in a given direction — it's a vector quantity.",
    "inertia": "Inertia is an object's resistance to a change in its state of motion.",
    "light": "Light is electromagnetic radiation visible to the human eye, traveling at about 299,792 km/s in a vacuum.",
    "sound": "Sound is a vibration that travels as a wave through a medium like air or water.",
    "magnetism": "Magnetism is a force produced by moving electric charges that can attract or repel certain materials.",

    # Chemistry
    "atom": "An atom is the smallest basic unit of matter, made up of protons, neutrons, and electrons.",
    "molecule": "A molecule is two or more atoms bonded together chemically.",
    "reaction": "A chemical reaction rearranges atoms to form new substances.",
    "element": "An element is a pure substance made of only one type of atom.",
    "compound": "A compound is a substance made of two or more elements chemically bonded together.",
    "acid": "An acid is a substance that releases hydrogen ions in water and has a pH below 7.",
    "base": "A base is a substance that accepts hydrogen ions and has a pH above 7.",
    "periodic table": "The periodic table organizes all known chemical elements by atomic number and properties.",
    "isotope": "An isotope is a variant of an element with the same number of protons but a different number of neutrons.",

    # Biology
    "cell": "A cell is the basic structural and functional unit of all living organisms.",
    "dna": "DNA (deoxyribonucleic acid) carries the genetic instructions for life.",
    "photosynthesis": "Photosynthesis is the process plants use to convert sunlight into chemical energy.",
    "bacteria": "Bacteria are single-celled microorganisms found almost everywhere on Earth.",
    "virus": "A virus is a tiny infectious agent that needs a host cell to reproduce.",
    "evolution": "Evolution is the process by which species change over generations through natural selection.",
    "ecosystem": "An ecosystem is a community of living organisms interacting with their physical environment.",
    "protein": "A protein is a large molecule made of amino acids that performs essential functions in living things.",
    "gene": "A gene is a segment of DNA that codes for a specific trait or function.",

    # Anatomy
    "heart": "The heart is a muscular organ that pumps blood through the circulatory system.",
    "brain": "The brain is the organ that controls the nervous system and processes thought, memory, and sensation.",
    "lungs": "The lungs are organs that exchange oxygen and carbon dioxide during breathing.",
    "stomach": "The stomach is an organ that digests food using acid and enzymes.",
    "muscle": "Muscles are tissues that contract to produce movement in the body.",
    "kidney": "Kidneys filter waste and excess fluid from the blood to produce urine.",
    "liver": "The liver processes nutrients, filters toxins, and produces bile for digestion.",
    "skeleton": "The skeleton is the internal framework of bones that supports and protects the body.",

    # Astronomy
    "star": "A star is a massive, luminous ball of hot gas held together by gravity, powered by nuclear fusion.",
    "planet": "A planet is a celestial body that orbits a star and has cleared its orbital path of debris.",
    "galaxy": "A galaxy is a massive collection of stars, gas, dust, and dark matter bound by gravity.",
    "black hole": "A black hole is a region of space where gravity is so strong that not even light can escape.",
    "supernova": "A supernova is the explosive death of a massive star.",
    "solar system": "The Solar System consists of the Sun and everything that orbits it, including eight planets.",
    "moon": "The Moon is Earth's only natural satellite, orbiting roughly every 27.3 days.",
    "asteroid": "An asteroid is a small rocky body orbiting the Sun, mostly found in the asteroid belt.",
    "comet": "A comet is an icy body that releases gas and dust, forming a glowing tail as it nears the Sun.",
    "milky way": "The Milky Way is the barred spiral galaxy that contains our Solar System.",

    # Geology
    "rock": "A rock is a solid mass made of one or more minerals.",
    "earthquake": "An earthquake is the shaking of the Earth's surface caused by sudden movement along a fault.",
    "volcano": "A volcano is an opening in the Earth's crust through which lava, gas, and ash erupt.",
    "tectonic plates": "Tectonic plates are large slabs of the Earth's crust that slowly move over the mantle.",
    "mineral": "A mineral is a naturally occurring inorganic solid with a defined chemical composition.",

    # Geography
    "usa": "The USA (United States of America) is a country of 50 states in North America.",
    "africa": "Africa is the second-largest continent, home to 54 countries.",
    "asia": "Asia is the largest and most populous continent on Earth.",
    "europe": "Europe is a continent known for its cultural diversity and dense concentration of countries.",
    "pacific ocean": "The Pacific Ocean is the largest and deepest ocean on Earth.",
    "atlantic ocean": "The Atlantic Ocean is the second-largest ocean, separating the Americas from Europe and Africa.",
    "amazon river": "The Amazon River is the largest river by discharge volume, flowing through South America.",
    "sahara": "The Sahara is the largest hot desert in the world, located in North Africa.",
    "everest": "Mount Everest is Earth's highest mountain above sea level, at 8,849 meters.",

    # English / Grammar
    "noun": "A noun is a word that names a person, place, thing, or idea.",
    "verb": "A verb is a word that expresses an action or state of being.",
    "adjective": "An adjective is a word that describes or modifies a noun.",
    "adverb": "An adverb is a word that modifies a verb, adjective, or another adverb.",
    "sentence": "A sentence is a group of words that expresses a complete thought.",
    "pronoun": "A pronoun is a word used in place of a noun, like 'he' or 'they'.",
    "synonym": "A synonym is a word that means the same, or nearly the same, as another word.",
    "antonym": "An antonym is a word that means the opposite of another word.",
    "metaphor": "A metaphor is a figure of speech that describes something by saying it is something else.",

    # Sports
    "soccer": "Soccer (football) is played by two teams trying to kick a ball into the opposing goal.",
    "basketball": "Basketball is played by two teams trying to shoot a ball through a hoop.",
    "football": "American football is played with an oval ball, teams advancing it toward end zones.",
    "baseball": "Baseball is played with a bat and ball, with teams taking turns batting and fielding.",
    "tennis": "Tennis is played by hitting a ball over a net using a racket.",
    "olympics": "The Olympics are international multi-sport events held every four years.",

    # Tech / Computer Science
    "algorithm": "An algorithm is a step-by-step set of instructions for solving a problem.",
    "internet": "The internet is a global network connecting computers to share information.",
    "software": "Software is a set of instructions or programs that tell a computer what to do.",
    "hardware": "Hardware refers to the physical components of a computer system.",
    "binary": "Binary is a base-2 number system using only 0s and 1s, used by computers.",
    "database": "A database is an organized collection of structured data stored electronically.",
    "artificial intelligence": "Artificial intelligence is the simulation of human-like reasoning and learning in machines.",
    "programming": "Programming is the process of writing instructions for a computer to execute.",

    # General science
    "science": "Science is the systematic study of the natural world through observation and experiment.",
    "hypothesis": "A hypothesis is a testable proposed explanation for an observation.",
    "experiment": "An experiment is a controlled test used to explore a hypothesis.",
    "theory": "A scientific theory is a well-substantiated explanation supported by extensive evidence.",

    # Misc / everyday
    "rainbow": "A rainbow is an optical effect caused by light refracting and reflecting in water droplets.",
    "tide": "Tides are the regular rise and fall of sea levels caused mainly by the Moon's gravity.",
    "climate change": "Climate change refers to long-term shifts in temperatures and weather patterns, largely driven by human activity.",
    "vaccine": "A vaccine trains the immune system to recognize and fight a specific pathogen.",
    "economy": "An economy is a system of production, distribution, and consumption of goods and services.",
    "democracy": "Democracy is a system of government where power is held by the people, typically through elected representatives.",
}

def tokenize(text):
    return re.findall(r"[a-z0-9']+", text.lower())

def knowledge_engine(text):
    tokens = set(tokenize(text))
    if not tokens:
        return None

    best_key, best_score, best_len = None, 0.0, 0
    for key in KNOWLEDGE:
        key_tokens = key.split()
        overlap = sum(1 for kt in key_tokens if kt in tokens)
        if overlap == 0:
            continue
        score = overlap / len(key_tokens)
        if score > best_score or (score == best_score and len(key_tokens) > best_len):
            best_score, best_key, best_len = score, key, len(key_tokens)

    if best_key and best_score >= 0.7:
        return KNOWLEDGE[best_key]

    # typo-tolerant fallback on single-word queries
    close = difflib.get_close_matches(text.lower().strip(), KNOWLEDGE.keys(), n=1, cutoff=0.8)
    if close:
        return KNOWLEDGE[close[0]]

    return None


# =====================================================================
# REASONING WRAPPER (adds a framing sentence for why/how/explain questions)
# =====================================================================
def reasoning_wrap(text, fact):
    t = text.lower()
    if t.startswith("why") or " why " in t:
        return f"Good question — here's the key reason: {fact}"
    if t.startswith("how"):
        return f"Here's how it works: {fact}"
    if "explain" in t:
        return f"Sure, let me explain: {fact}"
    return fact


# =====================================================================
# FRONTEND AND API ROUTES
# =====================================================================
@app.route("/", methods=["GET"])
def index():
    """Serve the chat interface at the application root."""
    return send_from_directory(app.root_path, "webai.html")


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json() or {}
    text = (data.get("message") or "").strip()
    session_id = data.get("session", "default")
    sess = get_session(session_id)

    if not text:
        return jsonify({"reply": "Say something and I'll do my best!"})

    sess["history"].append({"role": "user", "text": text})

    reply = smalltalk_engine(text)
    if not reply:
        reply = math_engine(text)
    if not reply:
        reply = unit_engine(text)
    if not reply:
        reply = time_engine(text)
    if not reply:
        reply = fun_engine(text, sess)
    if not reply:
        fact = knowledge_engine(text)
        if fact:
            reply = reasoning_wrap(text, fact)

    if not reply:
        reply = ("I don't have an answer for that one yet. I'm best at: quick math, unit "
                  "conversions, the time/date, jokes, fun facts, and short facts across "
                  "science, geography, history, grammar, and tech. Try rephrasing, or say "
                  "'help' to see what I can do!")

    sess["history"].append({"role": "assistant", "text": reply})
    if len(sess["history"]) > 40:
        sess["history"] = sess["history"][-40:]

    return jsonify({"reply": reply})


@app.route("/api/clear", methods=["POST"])
def clear_conversation():
    data = request.get_json() or {}
    session_id = data.get("session", "default")
    sessions.pop(session_id, None)
    return jsonify({"status": "cleared"})


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "mode": "offline — no API key required"})


if __name__ == "__main__":
    print("🧠 Free Offline Assistant starting — no API key needed, $0 forever.")
    app.run(host="0.0.0.0", port=5000, debug=False)
