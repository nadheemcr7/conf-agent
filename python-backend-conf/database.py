# database.py
import os
from supabase import create_client, Client
from dotenv import load_dotenv
import logging
from rapidfuzz import fuzz
from typing import Optional, List, Dict, Any

load_dotenv()

logger = logging.getLogger(__name__)

# Initialize the low-level Supabase client
url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_ANON_KEY")

if not url or not key:
    raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be set in environment variables")

# The actual Supabase client instance (internal to this module)
_raw_supabase_client: Client = create_client(url, key)

class CustomDatabaseClient:
    def __init__(self, client: Client):
        self._client = client
    
    def table(self, table_name: str):
        return self._client.table(table_name)

    async def query(self, table_name: str, select_fields: str = "*", filters: dict = None, 
                   order_by: list = None, limit: int = None, single: bool = False):
        """Query database with filters and options."""
        try:
            query = self._client.table(table_name).select(select_fields)
            
            # Apply filters
            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)
            
            # Apply ordering
            if order_by:
                for order in order_by:
                    column = order.get("column")
                    ascending = order.get("ascending", True)
                    query = query.order(column, desc=not ascending)
            
            # Apply limit
            if limit:
                query = query.limit(limit)
            
            # Execute query synchronously (Supabase Python client is sync)
            response = query.execute()
            
            if single:
                return response.data[0] if response.data else None
            return response.data
            
        except Exception as e:
            logger.error(f"Database query error: {e}", exc_info=True)
            raise e

# Create a single instance of your custom wrapper client
db_client: CustomDatabaseClient = CustomDatabaseClient(_raw_supabase_client)