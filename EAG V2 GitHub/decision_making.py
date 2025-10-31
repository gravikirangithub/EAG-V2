from typing import List
import logging
from models import DecisionContext, DecisionPlan, PlanStep

def make_plan(ctx: DecisionContext) -> DecisionPlan:
    log = logging.getLogger("agentpaint.decision")
    facts = ctx.facts
    steps: List[PlanStep] = []

    # Open Paint
    steps.append(PlanStep(action="open_paint", params={}))

    # Select color
    steps.append(PlanStep(action="select_color", params={"color": facts.color}))

    # Write user text
    steps.append(PlanStep(action="write_text", params={"text": facts.text}))
    plan = DecisionPlan(steps=steps)
    try:
        log.info("Planned %d steps", len(plan.steps))
    except Exception:
        pass
    return plan
