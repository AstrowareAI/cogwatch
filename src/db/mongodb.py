"""
MongoDB connection and utilities for Cogwatch
"""

import os
from pathlib import Path
from typing import Optional
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection
from dotenv import load_dotenv

# Load environment variables from .env file
# Look for .env in the project root (3 levels up from src/db/mongodb.py)
env_path = Path(__file__).parent.parent.parent / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    # Also try loading from current directory (for flexibility)
    load_dotenv()


def get_mongo_client(connection_string: Optional[str] = None) -> MongoClient:
    """
    Get MongoDB client instance
    
    Args:
        connection_string: MongoDB connection string. If None, reads from 
                         MONGODB_URI environment variable or uses default localhost
    
    Returns:
        MongoClient instance
    """
    if connection_string is None:
        connection_string = os.getenv(
            'MONGODB_URI', 
            'mongodb://localhost:27017/'
        )
    
    return MongoClient(connection_string)


def get_database(db_name: Optional[str] = None, client: Optional[MongoClient] = None) -> Database:
    """
    Get MongoDB database instance
    
    Args:
        db_name: Database name. If None, uses COGWATCH_DB_NAME env var or 'cogwatch'
        client: MongoDB client. If None, creates a new one
    
    Returns:
        Database instance
    """
    if db_name is None:
        db_name = os.getenv('COGWATCH_DB_NAME', 'cogwatch')
    
    if client is None:
        client = get_mongo_client()
    
    return client[db_name]


def get_collection(
    collection_name: str,
    db_name: Optional[str] = None,
    client: Optional[MongoClient] = None
) -> Collection:
    """
    Get MongoDB collection instance
    
    Args:
        collection_name: Name of the collection
        db_name: Database name. If None, uses COGWATCH_DB_NAME env var or 'cogwatch'
        client: MongoDB client. If None, creates a new one
    
    Returns:
        Collection instance
    """
    db = get_database(db_name=db_name, client=client)
    return db[collection_name]


def create_indexes(collection: Collection):
    """
    Create indexes for incidents collection
    
    Args:
        collection: MongoDB collection instance
    """
    # Index on incident_id (unique identifier from source)
    collection.create_index('incident_id', unique=True)
    
    # Index on date_modified for efficient date range queries
    collection.create_index('date_modified')
    
    # Index on created_at for initial import tracking
    collection.create_index('created_at')
    
    # Index on synced_at for sync tracking
    collection.create_index('synced_at')
    
    # Index on urgency_score (for future LLM scoring queries)
    collection.create_index('urgency_score')
    
    print(f"Created indexes on collection: {collection.name}")
