import os, json, re, logging
from typing import Dict, Any
from pydantic import BaseModel
from models import PerceptionInput, PerceptionOutput
from dotenv import load_dotenv

# Optional Gemini import
try:
    import google.generativeai as genai
except Exception:
    genai = None

load_dotenv()

# This prompt is crafted to meet the rubric in prompt_of_prompts-2.md:
# - Explicit reasoning instructions (think step-by-step)
# - Structured output (strict JSON schema)
# - Separation of reasoning and tools
# - Conversation loop / stop conditions
# - Internal self-checks and constraints
# - Domain grounding and safe failure behavior
PERCEPTION_SYSTEM_PROMPT = """
You are an extraction agent. Convert a user's request into structured JSON facts.

ROLE & GOAL
- ROLE: Perception layer that converts a natural request into machine-usable facts.
- GOAL: Output strict JSON stating the text to write and the color to use in MS Paint.

REASONING (think step-by-step, but DO NOT include your chain-of-thought in the final output)
1) Parse the user's prompt and find explicit text and color.
2) Validate color is in the allowed list provided.
3) If color is missing, select a default from the allowed list and note it.
4) Build a compact facts object.

OUTPUT FORMAT (MUST be valid JSON and nothing else)
{
  "intent": "write_text",
  "text": "<the exact user text>",
  "color": "<one_of_allowed_colors>",
  "quality_checks": {
    "validated_color": true/false,
    "notes": "<short explanation>"
  }
}

CONSTRAINTS
- Only produce the JSON object. No prose.
- Do not invent colors outside the allowed list.

TOOLS & COMPUTATION
- You do not perform any drawing here; only extraction. Tools are handled in later layers.

CONVERSATION LOOP / STOP
- Single-turn extraction. Produce one final JSON object and stop.

SELF-CHECKS
- Ensure the JSON parses and matches the schema exactly.
"""

def _strip_quotes(s: str) -> str:
    s = s.strip()
    if len(s) >= 2 and ((s[0] == '"' and s[-1] == '"') or (s[0] == "'" and s[-1] == "'")):
        return s[1:-1].strip()
    return s

def _safe_local_parse(text: str, allowed_colors) -> Dict[str, Any]:
    # Deterministic extraction from the structured prompt built in main.py
    # Looks for lines like: "- text: <value>" and "- color: <value>"
    user_text = None
    color = None

    try:
        m_text = re.search(r"^-\s*text:\s*(.+)$", text, re.MULTILINE)
        if m_text:
            user_text = _strip_quotes(m_text.group(1))
    except Exception:
        pass

    try:
        m_color = re.search(r"^-\s*color:\s*([a-zA-Z]+)\b", text, re.MULTILINE)
        if m_color:
            color = m_color.group(1).strip().lower()
    except Exception:
        pass

    # Fallbacks
    low = text.lower()
    if color not in allowed_colors:
        for c in allowed_colors:
            if c in low:
                color = c
                break
    if color is None and allowed_colors:
        color = allowed_colors[0]
    if not user_text:
        # Last resort: use the raw text but avoid passing the whole prompt; extract
        # everything after the "- text:" marker if present
        try:
            after = text.split("- text:", 1)[1].strip().splitlines()[0]
            user_text = _strip_quotes(after)
        except Exception:
            user_text = text.strip()

    return {
        "intent": "write_text",
        "text": user_text,
        "color": color,
        "quality_checks": {
            "validated_color": color in allowed_colors,
            "notes": "Local parser used."
        }
    }

class Perception:
    def __init__(self, allowed_colors):
        self.allowed_colors = allowed_colors
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.log = logging.getLogger("agentpaint.perception")

    def run(self, inp: PerceptionInput) -> PerceptionOutput:
        if genai and self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                model = genai.GenerativeModel("gemini-1.5-flash")  # lightweight & fast
                prompt = PERCEPTION_SYSTEM_PROMPT + "\n\nALLOWED COLORS: " + json.dumps(self.allowed_colors) + \
                         "\n\nUSER PROMPT:\n" + inp.prompt + "\n\nReturn only the JSON."
                self.log.info("Perception using Gemini backend")
                resp = model.generate_content(prompt)
                text = resp.text.strip()
                # Extract JSON
                first = text.find("{")
                last = text.rfind("}")
                if first != -1 and last != -1:
                    js = json.loads(text[first:last+1])
                    out = PerceptionOutput(**js)
                    self.log.info("Perception parsed: color=%s text_len=%d", out.color, len(out.text))
                    return out
            except Exception as e:
                # Fall back to local parsing
                self.log.warning("Perception Gemini failed, falling back: %s", e)
                parsed = _safe_local_parse(inp.prompt, self.allowed_colors)
                out = PerceptionOutput(**parsed)
                self.log.info("Perception fallback parsed: color=%s text_len=%d", out.color, len(out.text))
                return out
        # No API, fallback
        self.log.info("Perception using local parser")
        parsed = _safe_local_parse(inp.prompt, self.allowed_colors)
        out = PerceptionOutput(**parsed)
        self.log.info("Perception parsed: color=%s text_len=%d", out.color, len(out.text))
        return out
