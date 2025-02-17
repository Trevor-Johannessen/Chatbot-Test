import chromadb
import sys
import os
import json
import openai

database_location = ".\chroma.db"

# Open the Chroma database
chromadb_client = chromadb.PersistentClient(
        path=database_location
    )
collection = chromadb_client.get_collection(name="chat_context")

# Retrieve all documents in the collection
data = collection.get()
documents = data.get("documents", [])  # Extract the documents

# Display the documents
print("Documents in the collection:")
for doc in documents:
    print(doc)