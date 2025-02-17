import chromadb
import sys
import os
import json
from openai import OpenAI

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
database_location = os.getenv("CHROMADB")

def generate_embedding(text: str):
    response = openai_client.embeddings.create(
        input=text,
        model="text-embedding-ada-002"
    )
    embeddings = response.data[0].embedding
    return embeddings

# MAIN CODE BLOCK

# Open the Chroma database
chromadb_client = chromadb.PersistentClient(
        path=database_location
    )
collection = chromadb_client.get_or_create_collection(name="chat_context")

# Loop through arguments
for file in sys.argv[1:]:

    # Check that parameter leads to a file (not a directory)
    if not os.path.isfile(file):
        print(f"{file} cannot be found")
        continue

    # Read the given file (JSON format)
    try:
        with open(file, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError:
        print(f"{file} could not be parsed as JSON")
        continue

    # Ensure it has the proper attributes
    if 'id' not in data or type(data['id']) != str or data['id'] == '':
        print(f"{file} does not contain a valid 'id' attribute.")
        continue

    if 'text' not in data or type(data['text']) != str or data['text'] == '':
        print(f"{file} does not contain a valid 'text' attribute.")
        continue

    # Check for Metadata
    metadata = {}
    if 'metadata' in data:
        metadata = data['metadata']

    # Generate embeddings from the text
    embedding = generate_embedding(data['text'])

    # Add the document to the universal collection
    collection.add(
        documents=[data['text']],
        embeddings=[embedding],
        ids=[data['id']],
        metadatas=[metadata]
    )



