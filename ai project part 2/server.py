from flask import Flask, request, jsonify
from flask_cors import CORS

# ----------------- CREATE APP FIRST -----------------
app = Flask(__name__)
CORS(app)

# ----------------- MATH ENGINE -----------------

def math_engine(text):
    t = text.replace(" ", "")
    ops = ["+", "-", "*", "/"]
    if not any(op in t for op in ops):
        return None
    try:
        allowed = set("0123456789+-*/.")
        if not all(ch in allowed for ch in t):
            return None
        return str(eval(t))
    except:
        return None

# ----------------- GREETINGS -----------------

GREETINGS = {
    "hi": "Hey!",
    "hello": "Hello!",
    "hey": "Hey there!",
    "yo": "Yo!",
    "whatsup": "Not much, what’s up with you?",
    "sup": "Sup!",
    "bye": "See ya!",
    "seeya": "See ya!",
    "later": "Later!",
    "goodbye": "Goodbye!"
}

def greeting_engine(text):
    t = text.lower()
    for key, value in GREETINGS.items():
        if key in t:
            return value
    return None

# ----------------- KNOWLEDGE DOMAINS -----------------

PHYSICS = {
    "proton": "A proton is a positively charged particle found in the nucleus of an atom.",
    "neutron": "A neutron is a neutral particle found in the nucleus of an atom.",
    "electron": "An electron is a negatively charged particle orbiting the nucleus.",
    "photon": "A photon is a particle of light with no mass.",
    "gravity": "Gravity is the force that pulls objects toward each other.",
    "atom": "An atom is the basic unit of matter.",
    "energy": "Energy is the ability to do work or cause change.",
    "force": "Force is a push or pull on an object.",
    "speed": "Speed is how fast something moves.",
    "velocity": "Velocity is speed with direction.",
    "acceleration": "Acceleration is the change in velocity over time.",
    "thunder": "Thunder is the sound caused by rapid air expansion around lightning.",
    "lightning": "Lightning is a sudden electrical discharge in the atmosphere."
}

CODING = {
    "html": "HTML is the language used to structure content on web pages.",
    "css": "CSS styles web pages.",
    "javascript": "JavaScript powers interactive websites.",
    "python": "Python is a beginner‑friendly programming language.",
    "swift": "Swift is used to build Apple apps.",
    "xcode": "Xcode is Apple’s development environment.",
    "variable": "A variable stores a value.",
    "function": "A function is reusable code.",
    "loop": "A loop repeats code.",
    "class": "A class defines objects with properties and methods.",
    "compiler": "A compiler converts code into machine instructions."
}

BIOLOGY = {
    "cell": "A cell is the basic building block of life.",
    "dna": "DNA carries genetic information.",
    "organ": "An organ performs a specific function in the body.",
    "blood": "Blood carries oxygen and nutrients.",
    "tissue": "Tissues are groups of similar cells.",
    "bacteria": "Bacteria are single‑celled organisms.",
    "virus": "A virus is a tiny infectious agent that needs a host to reproduce."
}

ANATOMY = {
    "heart": "The heart pumps blood.",
    "brain": "The brain controls the body.",
    "lungs": "Lungs help you breathe.",
    "stomach": "The stomach digests food.",
    "kidney": "Kidneys filter blood.",
    "liver": "The liver processes nutrients.",
    "bone": "Bones support and protect the body.",
    "muscle": "Muscles help you move."
}

ASTRONOMY = {
    "star": "A star is a massive ball of hot gas.",
    "planet": "A planet orbits a star.",
    "galaxy": "A galaxy is a huge collection of stars.",
    "black hole": "A black hole has gravity so strong light cannot escape.",
    "nebula": "A nebula is a cloud of gas and dust.",
    "comet": "A comet is an icy object with a glowing tail.",
    "solar system": "The solar system is the Sun and the objects that orbit it.",
    "universe": "The universe contains everything that exists."
}

ASTROLOGY = {
    "astrology": "Astrology is the belief that celestial positions influence personality.",
    "zodiac": "The zodiac is a set of twelve signs.",
    "aries": "Aries is a zodiac sign.",
    "taurus": "Taurus is a zodiac sign.",
    "gemini": "Gemini is a zodiac sign.",
    "cancer": "Cancer is a zodiac sign.",
    "leo": "Leo is a zodiac sign.",
    "virgo": "Virgo is a zodiac sign.",
    "libra": "Libra is a zodiac sign.",
    "scorpio": "Scorpio is a zodiac sign.",
    "sagittarius": "Sagittarius is a zodiac sign.",
    "capricorn": "Capricorn is a zodiac sign.",
    "aquarius": "Aquarius is a zodiac sign.",
    "pisces": "Pisces is a zodiac sign."
}

GEOLOGY = {
    "rock": "Rocks are solid materials made of minerals.",
    "mineral": "A mineral is a natural solid with a specific structure.",
    "earthquake": "An earthquake is shaking caused by tectonic plates.",
    "volcano": "A volcano releases lava and gases.",
    "plate": "Tectonic plates move and cause earthquakes."
}

GEOGRAPHY = {
    "usa": "The USA is a country in North America.",
    "united states": "The United States is a country in North America.",
    "africa": "Africa is a continent south of Europe.",
    "europe": "Europe is a continent north of Africa.",
    "asia": "Asia is the largest continent.",
    "north america": "North America is a continent that includes the USA and Canada.",
    "south america": "South America is a continent south of North America.",
    "australia": "Australia is both a country and a continent.",
    "antarctica": "Antarctica is a frozen continent at the South Pole."
}

DOMAINS = [
    PHYSICS,
    CODING,
    BIOLOGY,
    ANATOMY,
    ASTRONOMY,
    ASTROLOGY,
    GEOLOGY,
    GEOGRAPHY
]

# ----------------- LOOKUP ENGINE -----------------

def lookup_any(text):
    t = text.lower()
    for domain in DOMAINS:
        for key, value in domain.items():
            if key in t:
                return value
    return None

# ----------------- PATTERN HANDLERS -----------------

def handle_what_is(text):
    t = text.lower()
    if not t.startswith("what is"):
        return None
    thing = t.replace("what is", "").strip()
    return lookup_any(thing)

def handle_where_is(text):
    t = text.lower()
    if not t.startswith("where is"):
        return None
    place = t.replace("where is", "").strip()
    return lookup_any(place)

# ----------------- MAIN ROUTE -----------------

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json()
    text = data.get("message", "")

    # greetings
    g = greeting_engine(text)
    if g:
        return jsonify({"reply": g})

    # math
    m = math_engine(text)
    if m:
        return jsonify({"reply": f"The result is {m}"})

    # what is
    w = handle_what_is(text)
    if w:
        return jsonify({"reply": w})

    # where is
    loc = handle_where_is(text)
    if loc:
        return jsonify({"reply": loc})

    # generic knowledge
    k = lookup_any(text)
    if k:
        return jsonify({"reply": k})

    return jsonify({"reply": "I'm a nerd in everything: math, physics, coding, biology, anatomy, astronomy, astrology, geology, geography, and general knowledge."})

# ----------------- RUN SERVER -----------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
