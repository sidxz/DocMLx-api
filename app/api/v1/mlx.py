import os
import shutil
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    BackgroundTasks,
    UploadFile,
    File,
)
from app.pipeline.presentation_summarization import gen_summary

router = APIRouter()


@router.post("/upload/")
async def upload_document(
    background_tasks: BackgroundTasks, file: UploadFile = File(...)
):
    # Fetch the upload directory from environment variables
    upload_directory = os.getenv("UPLOAD_DIRECTORY")
    if not upload_directory:
        raise HTTPException(
            status_code=500, detail="Upload directory is not configured."
        )

    # Construct the file path securely
    file_location = os.path.join(upload_directory, file.filename)

    try:
        # Save the uploaded file to the specified location
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        # Handle file save errors gracefully
        raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")

    # Add a background task to generate the summary for the uploaded document
    background_tasks.add_task(gen_summary, file_location)

    # Return the details of the uploaded file
    return {"filename": file.filename, "location": file_location}
