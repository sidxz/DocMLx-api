from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, UUID4
from typing import List, Optional
from uuid import uuid4
import pytz


class PipelineHistory(BaseModel):
    run_id: int
    step: str
    timestamp: datetime
    status: str
    details: Optional[str] = None


class Document(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    # Unique identifier for the document, automatically generated
    id: UUID4 = Field(
        default_factory=uuid4, title="The unique identifier of the prediction result"
    )
    run_id: Optional[int] = Field(
        0, title="The unique identifier of the prediction run"
    )

    # Required fields
    file_path: str = Field(..., title="The path to the input file")

    # Optional file-related fields
    file_type: Optional[str] = Field(None, title="The type of the input file")
    ext_path: Optional[str] = Field(None, title="The original path to the input file")
    doc_hash: Optional[str] = Field(None, title="The SHA-256 hash of the input file")
    link: Optional[str] = Field(None, title="The link to the input file")
    ext_id: Optional[str] = Field(
        None, title="The external identifier of the input file"
    )

    # Optional timestamps
    date_created: Optional[datetime] = Field(
        default_factory=lambda: datetime.now(pytz.utc),
        title="The date and time of the file upload",
    )
    date_updated: Optional[datetime] = Field(
        default_factory=lambda: datetime.now(pytz.utc),
        title="The date and time of the last update",
    )

    # Optional user-related fields
    created_by: Optional[str] = Field(None, title="The user who uploaded the file")
    updated_by: Optional[str] = Field(None, title="The user who last updated the file")

    # Optional document metadata
    author: Optional[str] = Field(None, title="The author of the document")
    date_published: Optional[datetime] = Field(
        None, title="The date of publication of the document"
    )

    authors: Optional[List[str]] = Field(
        default=None, description="List of extracted names of authors"
    )
    per_slide_summary: Optional[List[str]] = Field(
        default=None, description="List of summarized content of the slides"
    )
    short_summary: Optional[str] = Field(
        default=None, description="Short summary of the presentation"
    )
    executive_summary: Optional[str] = Field(
        default=None, description="Executive summary of the presentation"
    )
    title: Optional[str] = Field(None, title="The title of the document")

    target: Optional[str] = Field(None, title="The target of the document")
    stage: Optional[str] = Field(None, title="The stage of the document")

    # Optional tags associated with the document
    tags: List[str] = Field(
        default_factory=list, title="Tags associated with the document"
    )

    history: List[PipelineHistory] = Field(default_factory=list)
    run_date: Optional[datetime] = Field(
        default_factory=lambda: datetime.now(pytz.utc),
        title="The date and time of the run",
    )

    def add_history(
        self, run_id: int, step: str, status: str, details: Optional[str] = None
    ) -> None:
        """Add a new entry to the processing history."""
        utc_now = datetime.now(pytz.utc)
        self.history.append(
            PipelineHistory(
                run_id=run_id,
                step=step,
                timestamp=utc_now,
                status=status,
                details=details,
            )
        )

    def json_serializable(self) -> dict:
        """Convert the object to a JSON-serializable dictionary."""
        return {
            "id": self.id,
            "run_id": self.run_id,
            "file_path": self.file_path,
            "file_type": self.file_type,
            "ext_path": self.ext_path,
            "doc_hash": self.doc_hash,
            "link": self.link,
            "ext_id": self.ext_id,
            "date_created": (
                self.date_created.isoformat() if self.date_created else None
            ),
            "date_updated": (
                self.date_updated.isoformat() if self.date_updated else None
            ),
            "created_by": self.created_by,
            "updated_by": self.updated_by,
            "author": self.author,
            "date_published": (
                self.date_published.isoformat() if self.date_published else None
            ),
            "authors": self.authors,
            "per_slide_summary": self.per_slide_summary,
            "short_summary": self.short_summary,
            "executive_summary": self.executive_summary,
            "target": self.target,
            "stage": self.stage,
            "title": self.title,
            "tags": self.tags,
            "run_date": self.run_date.isoformat() if self.run_date else None,
            "history": [entry.model_dump() for entry in self.history],
        }
