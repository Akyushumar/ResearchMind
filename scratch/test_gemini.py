import os
from google import genai

client = genai.Client()
response = client.models.embed_content(
    model='gemini-embedding-2',
    contents='Test string',
    config={"output_dimensionality": 10}
)
print(len(response.embeddings[0].values))

