from pydantic import BaseModel, Field


class Topic(BaseModel):
    topic: str = Field(description="topic section of the document")