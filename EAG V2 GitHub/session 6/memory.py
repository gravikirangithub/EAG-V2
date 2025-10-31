from pydantic import BaseModel
from typing import List
from models import MemoryStore, ColorName

class StaticMemory(BaseModel):
    store: MemoryStore = MemoryStore(
        colors=[
            "red","green","blue","yellow","black","white","orange","purple","pink","brown","gray"
        ]
    )

    def list_colors(self) -> List[ColorName]:
        return list(self.store.colors)
