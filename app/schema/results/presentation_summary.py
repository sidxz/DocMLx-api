from typing import List, Optional
from pydantic import BaseModel, Field


class PresentationSummary(BaseModel):
    authors: Optional[List[str]] = Field(
        default=None, description="List of extracted names of authors"
    )
    title: Optional[str] = Field(default=None, description="Title of the presentation")
    per_slide_summary: Optional[List[str]] = Field(
        default=None, description="List of summarized content of the slides"
    )

    def print(self) -> None:
        """
        Prints the PresentationSummary object in a nicely formatted way.
        """
        print("\nPresentation Summary")
        print("=" * 20)

        # Print authors
        print("Authors:")
        if self.authors:
            for author in self.authors:
                print(f"  - {author}")
        else:
            print("  No authors found.")

        # Print title
        print("\nTitle:")
        if self.title:
            print(f"  {self.title}")
        else:
            print("  No title available.")

        # Print per-slide summary
        print("\nPer-Slide Summary:")
        if self.per_slide_summary:
            for i, slide_summary in enumerate(self.per_slide_summary, start=1):
                print(f"  Slide {i}: {slide_summary}")
        else:
            print("  No slide summaries available.")
        print("=" * 20)
