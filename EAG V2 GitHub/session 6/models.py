from pydantic import BaseModel, Field
from typing import List, Literal, Dict, Any

ColorName = Literal["red","green","blue","yellow","black","white","orange","purple","pink","brown","gray"]

class UserPreferences(BaseModel):
    text: str
    color: ColorName

class PerceptionInput(BaseModel):
    # The human-facing prompt that includes user's text and chosen color
    prompt: str

class PerceptionOutput(BaseModel):
    # Clean facts extracted from the prompt
    intent: Literal["write_text"]
    text: str
    color: ColorName
    quality_checks: Dict[str, Any] = Field(default_factory=dict)

class MemoryStore(BaseModel):
    colors: List[ColorName]

class DecisionContext(BaseModel):
    facts: PerceptionOutput
    memory: MemoryStore

class PlanStep(BaseModel):
    action: Literal["open_paint","select_color","write_text","close_paint","noop"]
    params: Dict[str, Any] = Field(default_factory=dict)

class DecisionPlan(BaseModel):
    steps: List[PlanStep]

class ActionResult(BaseModel):
    success: bool
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)
