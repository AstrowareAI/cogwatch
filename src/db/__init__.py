"""
Database utilities for Cogwatch
"""

from .mongodb import get_mongo_client, get_collection

__all__ = ['get_mongo_client', 'get_collection']
