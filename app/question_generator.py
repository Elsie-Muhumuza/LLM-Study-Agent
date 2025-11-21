# app/question_generator.py
"""
Question generation interface.

Primary: Gemini (via Google Generative API/HTTP). If GEMINI not configured, fallback to OpenAI (if OPENAI_API_KEY present).
If neither available, fallback to deterministic template generator.

Note: You must set environment variable GEMINI_API_KEY for Gemini usage (or configure OpenAI).
"""

import os
import textwrap
from typing import List
import json
import requests  # lightweight HTTP client

# NOTE: You must add your GEMINI API key as GEMINI_API_KEY and configure endpoint if using Google's Generative API.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

PERMANENT_QS = [
    "🔎 *What does this passage tell us about God?*",
    "👤 *What does this passage tell us about humanity (man)?*"
]

def _heuristic_questions(title: str, reference: str) -> List[str]:
    qs = [
        f"1️⃣ *Observation:* What is happening in *{title}* ({reference})? List 2–3 facts.",
        f"2️⃣ *Context:* Who is the speaker/audience in this passage?",
        f"3️⃣ *Meaning:* What could the key images in the passage symbolize?",
        f"4️⃣ *Cross-ref:* Does this connect with another scripture? Which and why?",
        f"5️⃣ *Character:* Which character stands out and why?",
        f"6️⃣ *Personal application:* How could this passage affect your life this week?",
        f"7️⃣ *Community application:* How could our fellowship live this truth out together?",
        f"8️⃣ *Challenge:* Is there a practical task to try this week?",
        f"9️⃣ *Difficulties:* What is confusing or challenging in this passage?",
        f"🔟 *One-line summary:* Summarize the main message in one sentence."
    ]
    return qs + PERMANENT_QS

def _call_gemini(prompt: str) -> str:
    """
    Minimal example for calling a Gemini-like API (replace endpoint & headers with the one you use).
    This is a placeholder demonstrating the expected HTTP call pattern.
    """
    api_key = GEMINI_API_KEY
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set.")
    # Example endpoint — replace with actual Generative API endpoint you will use
    endpoint = "https://api.generativeai.example/v1/generate"  # <-- replace with real endpoint
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {"prompt": prompt, "max_tokens": 800}
    r = requests.post(endpoint, headers=headers, json=payload, timeout=30)
    r.raise_for_status()
    data = r.json()
    # adapt to the response shape your provider returns; below assumes data["text"]
    return data.get("text") or data.get("generation") or json.dumps(data)

def _call_openai(prompt: str) -> str:
    import openai
    openai.api_key = OPENAI_API_KEY
    resp = openai.ChatCompletion.create(
        model="gpt-4o-mini", messages=[{"role":"user","content":prompt}], max_tokens=800
    )
    return resp.choices[0].message.content

def generate_questions(title: str, reference: str) -> List[str]:
    """
    Generate 10 questions + 2 permanent questions. Uses Gemini if configured, else OpenAI, else heuristic.
    Returns list of strings.
    """
    prompt = textwrap.dedent(f"""
    You are a helpful Bible study leader. Produce 10 clear, age-adult appropriate, discussion questions
    about the passage titled "{title}" ({reference}). Use concise language, include emojis to make the list readable, 
    and end with the two permanent questions:
    1) What does this passage tell us about God?
    2) What does this passage tell us about man?

    Number the questions 1 to 10, then include the two permanent questions as separate bullets.
    Keep total length under 600 words.
    """)
    try:
        if GEMINI_API_KEY:
            out = _call_gemini(prompt)
            # Try to split lines into items; fall back to heuristic if parsing fails
            items = [line.strip() for line in out.splitlines() if line.strip()]
            if len(items) >= 12:
                return items[:12]
            # fallback to returning the full text as single item split by newline
            return items or _heuristic_questions(title, reference)
        elif OPENAI_API_KEY:
            out = _call_openai(prompt)
            items = [line.strip() for line in out.splitlines() if line.strip()]
            return items if items else _heuristic_questions(title, reference)
        else:
            return _heuristic_questions(title, reference)
    except Exception as e:
        # On any error, fallback to deterministic generator
        print("LLM generation failed, falling back to heuristics:", e)
        return _heuristic_questions(title, reference)
