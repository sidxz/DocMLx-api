import os
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from fastapi import HTTPException

# Load MongoDB configuration from environment variables
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "docmlx")

# Async MongoDB Client (Motor)
class AsyncMongoDB:
    client: AsyncIOMotorClient = None

    @classmethod
    async def connect(cls):
        """Establish an async connection to the MongoDB database."""
        if cls.client is None:
            try:
                cls.client = AsyncIOMotorClient(MONGO_URI, uuidRepresentation='standard')
                logging.info("Connected to MongoDB (async)")
            except Exception as e:
                logging.error(f"Failed to connect to MongoDB (async): {e}")
                raise HTTPException(status_code=500, detail="Could not connect to MongoDB")
        return cls.client[MONGO_DB]

    @classmethod
    async def close_connection(cls):
        """Close the async MongoDB connection."""
        if cls.client:
            cls.client.close()
            cls.client = None
            logging.info("Async MongoDB connection closed")

async def get_async_collection(collection_name: str):
    """Utility function to get an async MongoDB collection."""
    db = await AsyncMongoDB.connect()
    return db[collection_name]

# Synchronous MongoDB Client (pymongo)
class SyncMongoDB:
    client: MongoClient = None

    @classmethod
    def connect(cls):
        """Establish a synchronous connection to the MongoDB database."""
        if cls.client is None:
            try:
                cls.client = MongoClient(MONGO_URI, uuidRepresentation='standard')
                logging.info("Connected to MongoDB (sync)")
            except PyMongoError as e:
                logging.error(f"Failed to connect to MongoDB (sync): {e}")
                raise HTTPException(status_code=500, detail="Could not connect to MongoDB")
        return cls.client[MONGO_DB]

    @classmethod
    def close_connection(cls):
        """Close the synchronous MongoDB connection."""
        if cls.client:
            cls.client.close()
            cls.client = None
            logging.info("Sync MongoDB connection closed")

def get_sync_collection(collection_name: str):
    """Utility function to get a synchronous MongoDB collection."""
    db = SyncMongoDB.connect()
    return db[collection_name]
