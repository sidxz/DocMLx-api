from typing import List
from pydantic import BaseModel, Field


class AuthorNames(BaseModel):
    names: List[str] = Field(description="list of extracted names of authors")