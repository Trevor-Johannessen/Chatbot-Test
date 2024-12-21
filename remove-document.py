import chromadb
import os
import sys

database_location = os.getenv("CHROMADB")
chromadb_client = chromadb.PersistentClient(
        path=database_location
    )
collection = chromadb_client.get_or_create_collection(name="chat_context")
collection.delete(ids=sys.argv[1:])