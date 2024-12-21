import chromadb
import os
from openai import OpenAI
import requests
import json

# Globals
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
database_location = os.getenv("CHROMADB")
ollama_api_url = os.getenv("OLLAMA_API")
ollama_api_key = os.getenv("OLLAMA_API_KEY")

# Open the Chroma database
chromadb_client = chromadb.PersistentClient(
        path=database_location
    )
collection = chromadb_client.get_or_create_collection(name="chat_context")

def generate_embedding(text: str):
    response = openai_client.embeddings.create(
        input=text,
        model="text-embedding-ada-002"
    )
    embeddings = response.data[0].embedding
    return embeddings

def prompt(query):
    # Get embedding from query
    query_embedding = generate_embedding(query)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=5  # Adjust as needed
    )
    
    # Format query
    relevant_contexts = [res["document"] for res in results["documents"] if "document" in res]
    optional_context = ""
    if relevant_contexts != []:
        optional_context = f"""
You may use the following context to help answer the given prompt:

Context:
    {relevant_contexts}

Question:
"""

    prompt = f"""
    {optional_context}
    {query}
    """

    # Send request to Ollama
    response = requests.post(
        f"http://{ollama_api_url}/api/generate",
        json={
                "model": "llama3.2:latest",
                "prompt": prompt,
                # "stream": "false"
            },
    )
    if response.status_code != 200:
        print(f"Error: status code (${response.status_code})")
    words = [json.loads(row.decode("utf-8")) for row in response.content.split(b"\n") if row]
    for word in words:
        if word['done']:
            break
        print(word['response'], end='')
    print("")

prompt_text = "Prompt: "
query = input(prompt_text)
while query != "Goodbye":
    prompt(query)
    query = input(prompt_text)