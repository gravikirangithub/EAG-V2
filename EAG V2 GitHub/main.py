import os
import logging
from dotenv import load_dotenv
from models import UserPreferences, PerceptionInput, DecisionContext
from memory import StaticMemory
from perception import Perception
from decision_making import make_plan
from action import run_actions

def ask_user_prefs(mem: StaticMemory) -> UserPreferences:
    print("Welcome! Before we start, please enter your text and choose a color.")
    user_text = input("Enter the text to write in Paint, then press Enter: ").strip()
    while not user_text:
        user_text = input("Text cannot be empty. Enter the text: ").strip()

    print("Available colors:", ", ".join(mem.list_colors()))
    color = input("Pick a color from the list: ").strip().lower()
    while color not in mem.list_colors():
        print("Invalid color. Try again.")
        color = input("Pick a color from the list: ").strip().lower()

    return UserPreferences(text=user_text, color=color)

def build_user_prompt(prefs: UserPreferences, mem: StaticMemory) -> str:
    return f"""
User wants to write text in MS Paint.

Preferences (must be respected):
- text: {prefs.text}
- color: {prefs.color}

Allowed colors: {mem.list_colors()}

Task: Extract clean facts (text + color) and return strict JSON as specified.
""".strip()

def main():
    load_dotenv()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    log = logging.getLogger("agentpaint")
    log.info("AgentPaint starting up")
    mem = StaticMemory()
    prefs = ask_user_prefs(mem)
    log.info("Collected user preferences: text_len=%d, color=%s", len(prefs.text), prefs.color)

    # Perception
    prompt = build_user_prompt(prefs, mem)
    log.info("Phase: perception -> extracting facts from prompt")
    perception = Perception(allowed_colors=mem.list_colors())
    facts = perception.run(PerceptionInput(prompt=prompt))
    log.info("Perception output: intent=%s color=%s text_len=%d",
             getattr(facts, "intent", "?"), getattr(facts, "color", "?"), len(getattr(facts, "text", "")))

    # Decision-Making
    log.info("Phase: decision -> building plan")
    ctx = DecisionContext(facts=facts, memory=mem.store)
    plan = make_plan(ctx)
    try:
        step_names = [s.action for s in plan.steps]
    except Exception:
        step_names = []
    log.info("Decision plan steps: %s", step_names)

    # Action
    log.info("Phase: action -> executing plan")
    result = run_actions(plan)
    log.info("Action result: success=%s message=%s", result.success, result.message)
    print(f"Done: {result.success} - {result.message}")

if __name__ == "__main__":
    main()
