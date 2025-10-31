# AgentPaint – Perception → Memory → Decision → Action

A tiny AI Agent that asks your preferences first (color and shape), then runs an agentic flow:

1. **Perception (LLM)** — builds a structured “facts” object from your prompt using a strong prompt that meets `prompt_of_prompts-2.md` quality checks. Uses Google Gemini if available, otherwise falls back to a deterministic parser.
2. **Memory** — static Pydantic store of known colors.
3. **Decision-Making** — plans writing steps for MS Paint based on Perception facts + Memory.
4. **Action** — opens MS Paint, write the text on the canvas with chosen color.



---

## Quick Start (Windows)

1. **Python**: 3.10+ recommended
2. **Install**:
   ```bash
   pip install -r requirements.txt
   ```
3. **(Optional) Gemini**: set your key for best Perception
   ```bash
   setx GEMINI_API_KEY "your_key_here"
   ```
4. **Run**:
   ```bash
   python main.py
   ```

You’ll be asked to pick a **color** from the Memory list. The agent will then open **MS Paint**, write the text with chosen color.

---

## Files

- `main.py` — wires the stages in order: **Perception → Memory → Decision → Action**.
- `models.py` — all Pydantic data models for I/O between layers.
- `memory.py` — static Memory store of allowed colors and shapes (Pydantic model).
- `perception.py` — builds a robust LLM prompt and extracts structured facts from your inputs. Falls back to a parser if no Gemini.
- `decision_making.py` — translates facts + memory into a concrete plan for drawing and annotating in Paint.
- `action.py` — executes the plan using `pywinauto` + `pyautogui` to control Paint.
- `requirements.txt` — dependencies.
- `utils/win_paint.py` — helpers to interact with Paint reliably.
- `.env.example` — example environment vars for Gemini.

---

## Known Notes

- This uses approximate UI interactions for Paint and may vary by Windows build / DPI scaling. The code includes retries and best-effort selectors. If your UI differs, adjust offsets in `utils/win_paint.py`.
