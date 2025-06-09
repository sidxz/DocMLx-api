from typing import List, Union
from fastapi import HTTPException, status
from pydantic import UUID4
from pymongo.errors import PyMongoError
from app.core.mongo_config import get_sync_collection
from app.schema.results.document import Document
from app.core.logging_config import logger


def save_document_sync(document: Document) -> UUID4:
    """
    Save document metadata to MongoDB synchronously.
    If a document with the same ID exists, update it. Otherwise, insert a new document.
    """
    logger.info("Saving document to MongoDB (sync)")
    try:
        collection = get_sync_collection("documents")
        doc_json = document.json_serializable()
        
        # Check if the document already exists
        result = collection.replace_one({"id": document.id}, doc_json, upsert=True)
        
        if result.matched_count > 0:
            logger.info(f"Updated existing document with ID: {document.id}")
        else:
            logger.info(f"Inserted new document with ID: {document.id}")
        
        return document.id
    except PyMongoError as e:
        logger.error(f"Failed to save document (sync): {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save document: {str(e)}"
        )
    

def get_all_documents_sync() -> List[Document]:
    """
    Retrieve all documents from the collection.

    Returns:
        List[Document]: A list of all documents.
    """
    try:
        collection = get_sync_collection("documents")

        logger.debug("Retrieving all documents from collection")

        cursor = collection.find({})
        return [Document(**doc) for doc in cursor]

    except PyMongoError as e:
        logger.error(f"Error retrieving all documents (sync): {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving all documents: {str(e)}",
        )


def get_documents_by_authors_sync(authors: List[str]) -> List[Document]:
    """
    Retrieve documents that include any of the given authors (case-insensitive and partial match).
    
    Args:
        authors (List[str]): A list of author names to search for.

    Returns:
        List[Document]: A list of matched documents.
    """
    try:
        collection = get_sync_collection("documents")

        # Build a list of regex filters for partial, case-insensitive matching
        regex_conditions = [
            {"authors": {"$elemMatch": {"$regex": author, "$options": "i"}}}
            for author in authors
        ]

        query = {"$or": regex_conditions}

        logger.debug(f"Running author search with query: {query}")

        cursor = collection.find(query)
        return [Document(**doc) for doc in cursor]

    except PyMongoError as e:
        logger.error(f"Error retrieving documents by authors (sync): {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving documents by authors: {str(e)}",
        )

def get_document_by_field_sync(field: str, value: Union[str, UUID4, List[str]]) -> Document:
    """
    Retrieve a document from MongoDB based on a specified field and value synchronously.
    """
    try:
        collection = get_sync_collection("documents")
        query = {field: value}
        document = collection.find_one(query)
        if document:
            return Document(**document)
        else:
            return None
    except PyMongoError as e:
        logger.error(f"Error retrieving document (sync): {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving document: {str(e)}",
        )


def get_document_by_id_sync(doc_id: UUID4) -> Document:
    """Retrieve a document by its ID synchronously."""
    return get_document_by_field_sync("id", doc_id)


def get_document_by_hash_sync(doc_hash: str) -> Document:
    """Retrieve a document by its hash synchronously."""
    return get_document_by_field_sync("doc_hash", doc_hash)


def get_document_by_filename_sync(filename: str) -> Document:
    """Retrieve a document by its filename synchronously."""
    return get_document_by_field_sync("filename", filename)


def get_document_by_file_path_sync(file_path: str) -> Document:
    """Retrieve a document by its file path synchronously."""
    return get_document_by_field_sync("file_path", file_path)


def get_documents_by_tags_sync(tags: List[str]) -> List[Document]:
    """Retrieve documents by tags synchronously."""
    try:
        collection = get_sync_collection("documents")
        cursor = collection.find({"tags": {"$in": tags}})
        return [Document(**doc) for doc in cursor]
    except PyMongoError as e:
        logger.error(f"Error retrieving documents by tags (sync): {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving documents: {str(e)}",
        )