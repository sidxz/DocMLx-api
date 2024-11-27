from typing import List
from pydantic import BaseModel, Field


class Target(BaseModel):
    target: str = Field(
        description="Name of the protein of a drug target of Mycobacterium tuberculosis"
    )
