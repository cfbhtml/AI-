from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import math
import sympy as sp

app = Flask(__name__)
CORS(app)

sessions = {"default": []}

# ---------- CORE SMART REPLY ----------

def smart_reply(user_text):
    text = user_text.lower().strip()

    # greetings
    if text in ["hi", "hello", "hey", "yo", "sup"]:
        return "Hi! I'm your math + physics + explainer AI. Ask me something."

    # calculus: derivative
    if text.startswith("derivative of"):
        expr_str = text.replace("derivative of", "").strip()
        x = sp.symbols("x")
        try:
            expr = sp.sympify(expr_str)
            deriv = sp.diff(expr, x)
            return f"The derivative of {expr_str} with respect to x is: {sp.simplify(deriv)}"
        except Exception:
            return "I couldn't parse that expression. Try: derivative of x^2, derivative of sin(x), derivative of x^3 + 2x."

    # calculus: integral
    if text.startswith("integral of"):
        expr_str = text.replace("integral of", "").strip()
        x = sp.symbols("x")
        try:
            expr = sp.sympify(expr_str)
            integ = sp.integrate(expr, x)
            return f"An antiderivative of {expr_str} with respect to x is: {integ} + C"
        except Exception:
            return "I couldn't parse that expression. Try: integral of x, integral of cos(x), integral of 3x^2."

    # general math expression (calculator mode)
    try:
        if any(char.isdigit() for char in text):
            expr = sp.sympify(text)
            result = expr.evalf()
            return f"The result is {result}"
    except Exception:
        pass

    # physics helper
    physics_answer = physics_helper(text)
    if physics_answer:
        return physics_answer

    # general questions
    if any(q in text for q in ["what", "why", "how", "who", "when", "where"]):
        return explain_question(text)

    # fallback
    return "I'm here. Ask me a math question (2+2, derivative of x^2), a physics question (speed, energy), or a science question."

# ---------- PHYSICS HELPER ----------

def physics_helper(text):
    # very simple physics patterns

    if "speed" in text or "velocity" in text:
        return "Speed (or velocity) is distance divided by time. Formula: v = d / t."

    if "acceleration" in text:
        return "Acceleration is the change in velocity over time. Formula: a = Δv / Δt."

    if "force" in text and "mass" in text and "acceleration" in text:
        return "Force is mass times acceleration. Formula: F = m * a."

    if "force" in text and "newton" in text:
        return "A newton (N) is the unit of force. 1 N = 1 kg·m/s²."

    if "kinetic energy" in text or ("energy" in text and "motion" in text):
        return "Kinetic energy is the energy of motion. Formula: KE = 1/2 * m * v^2."

    if "potential energy" in text and "gravity" in text:
        return "Gravitational potential energy near Earth's surface: PE = m * g * h."

    if "momentum" in text:
        return "Momentum is mass times velocity. Formula: p = m * v."

    return None

# ---------- GENERAL EXPLAINER ----------

def explain_question(text):
    if "gravity" in text:
        return "Gravity is the force that pulls objects toward each other. It keeps you on the ground and makes planets orbit stars."

    if "sky" in text and "blue" in text:
        return "The sky looks blue because sunlight scatters in the atmosphere. Blue light scatters more than other colors."

    if "star" in text:
        return "A star is a huge ball of hot gas that produces light and heat through nuclear fusion."

    if "planet" in text:
        return "A planet is a large object that orbits a star. Earth is a planet that orbits the Sun."

    if "cloud" in text:
        return "Clouds are made of tiny water droplets or ice crystals floating in the air."

    if "sun" in text:
        return "The Sun is a star at the center of our solar system. It gives Earth light and heat."

    if "moon" in text:
        return "The Moon is Earth's natural satellite. It reflects sunlight and affects ocean tides."

    if "tree" in text:
        return "Trees are plants that use sunlight to make food. They produce oxygen, which humans need to breathe."

    if "computer" in text:
        return "A computer is a machine that processes information using hardware and software."

    if "ai" in text:
        return "AI (artificial intelligence) is software that can learn patterns and make decisions or predictions."

    return "That's a good question. I can explain science, nature, space, technology, math, and basic physics. Try asking:\n- Why is the sky blue\n- What is gravity\n- Derivative of x^2\n- What is kinetic energy"

# ---------- FLASK ROUTE ----------

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json()
    session_id = data.get("session", "default")
    user_text = data.get("message", "").strip()

    if not user_text:
        return jsonify({"error": "Empty message"}), 400

    sessions.setdefault(session_id, []).append({
        "role": "user",
        "text": user_text,
        "time": datetime.now().isoformat()
    })

    reply_text = smart_reply(user_text)

    sessions[session_id].append({
        "role": "assistant",
        "text": reply_text,
        "time": datetime.now().isoformat()
    })

    return jsonify({"reply": reply_text})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
