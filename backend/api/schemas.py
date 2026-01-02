from pydantic import BaseModel
from typing import Optional

class Action(BaseModel):
    action: str
    amount: Optional[int] = 0
