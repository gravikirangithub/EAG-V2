from typing import Dict, Any
import logging
from models import DecisionPlan, ActionResult
from utils.win_paint import (
    launch_paint, _get_app_and_window,
    click_palette_color, write_text, close_paint
)
import time

def run_actions(plan: DecisionPlan) -> ActionResult:
    log = logging.getLogger("agentpaint.action")
    try:
        win = None
        for step in plan.steps:
            if step.action == "open_paint":
                log.info("Action: open_paint")
                launch_paint()
                _, win = _get_app_and_window()
                if not win:
                    log.error("Failed to attach to Paint window")
                    return ActionResult(success=False, message="Could not attach to Paint window.", details={})
            elif step.action == "select_color":
                color = step.params.get("color","red")
                log.info("Action: select_color -> %s", color)
                click_palette_color(win, color)
            elif step.action == "write_text":
                txt = step.params.get("text", "")
                log.info("Action: write_text (len=%d)", len(txt))
                write_text(win, txt)
            elif step.action == "close_paint":
                log.info("Action: close_paint")
                close_paint(win)

        log.info("Action pipeline completed")
        return ActionResult(success=True, message="Actions executed.", details={})
    except Exception as e:
        log.exception("Action pipeline error")
        return ActionResult(success=False, message=f"Action error: {e}", details={})
