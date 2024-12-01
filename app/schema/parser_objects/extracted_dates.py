from typing import List
from pydantic import BaseModel, Field


class ExtractedDates(BaseModel):
    dates: List[str] = Field(description="List of extracted dates in ISO format (YYYY-MM-DD)")
