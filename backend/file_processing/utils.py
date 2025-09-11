from google import genai


def generate_upload_blob_name(user_id, file_name):
    return f"django-uploads/{user_id}/{file_name}"


def embed_content(content: str | list[str]) -> list[float]:
    client = genai.Client()
    result = client.models.embed_content(model="gemini-embedding-001", contents=content)
    return result.embeddings
