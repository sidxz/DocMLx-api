from typing import List
from pydantic import BaseModel, Field


class PresentationSummary(BaseModel):
    names: List[str] = Field(description="list of extracted names of authors")
    title: str = Field(description="title of the presentation")