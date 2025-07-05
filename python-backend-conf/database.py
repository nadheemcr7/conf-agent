# database.py
import os
from supabase import create_client, Client
from dotenv import load_dotenv
import logging
from rapidfuzz import fuzz # Import fuzz for use in potential future wrapper enhancements
from typing import Optional, List, Dict, Any

load_dotenv()

logger = logging.getLogger(__name__)

# Initialize the low-level Supabase client
url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_ANON_KEY") # Assuming you are using ANON key for public access

if not url or not key:
    raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be set in environment variables")

# The actual Supabase client instance (internal to this module)
_raw_supabase_client: Client = create_client(url, key)

class CustomDatabaseClient:
    def __init__(self, client: Client):
        self._client = client # Store the raw Supabase client internally
    
    # --- IMPORTANT FIX: Expose the raw client's table method ---
    # This allows you to do db_client.table("users").select(...)
    def table(self, table_name: str):
        return self._client.table(table_name)

    async def query(self, table_name: str, select_fields: str = "*", filters: dict = None, 
                   order_by: list = None, limit: int = None, single: bool = False):
        """Query database with filters and options.
        
        Args:
            table_name (str): The name of the table to query.
            select_fields (str): Fields to select (e.g., "id, name").
            filters (dict): Dictionary of filters (e.g., {"column": "value"}).
                            Supports 'details->>field' for JSONB fields.
            order_by (list): List of dictionaries for ordering (e.g., [{"column": "name", "ascending": True}]).
            limit (int): Maximum number of records to return.
            single (bool): If true, returns the first record or None.
        """
        try:
            query = self._client.table(table_name).select(select_fields)
            
            # Apply filters
            if filters:
                for key, value in filters.items():
                    # Handle JSONB filtering explicitly if needed here,
                    # otherwise Supabase client's .filter will work for 'details->>registration_id'
                    # if the key is formatted correctly.
                    # For example: query = query.eq(key, value) directly works for 'details->>registration_id'
                    # as it's just a string comparison.
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
            
            # Execute query - ensure it's awaited if the underlying Supabase client is async
            response = await query.execute()
            
            if single:
                return response.data[0] if response.data else None
            return response.data
            
        except Exception as e:
            logger.error(f"Database query error in CustomDatabaseClient.query: {e}", exc_info=True)
            raise e

# Create a single instance of your custom wrapper client
db_client: CustomDatabaseClient = CustomDatabaseClient(_raw_supabase_client)

# You do NOT need the old 'db_client: Client = create_client(url, key)' line after this
# as it would be shadowed by the class instance.
# The variable name 'db_client' is now your CustomDatabaseClient instance.