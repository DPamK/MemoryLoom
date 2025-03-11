from pydantic import BaseModel, Field
from typing import Literal, Optional

class Message(BaseModel):
    role: Literal["user", "assistant", "system", "function"] = Field(..., description="消息角色")
    name: str = Field(None, description="sender名称")
    content: str = Field(..., description="消息内容")

    def  __str__(self):
        return f"{self.name}({self.role}): {self.content}"
