from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP
import os

# Initialize FastMCP server
mcp = FastMCP("knowledge")


TOKEN = os.getenv("KNOWLEDGE_USER_TOKEN")


async def make_get_chunks_request(query: str) -> dict[str, Any] | None:
    """
    Make a request to the knowledge API
    """

    url = "https://knowledge-server-372502133685.europe-west4.run.app/get-chunks/"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                url,
                headers={"Authorization": f"Token {TOKEN}"},
                data={"query": query},
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()
        except Exception:
            return None


def format_chunks(chunks: list[str]) -> str:
    return "\n---\n".join(chunks)


async def get_chunks(query: str) -> str:
    """
    Retrieves the relevant information it the form of text chunks, from the knowledge API,
    or informs about the failure to retrieve data.
    """
    data = await make_get_chunks_request(query)
    if data is None:
        return "Failed to retrieve data from the knowledge API..."
    content_field_name = "contents"
    chunks = data.get(content_field_name, None)
    if chunks is None:
        return f'Could not find the "{content_field_name}" field in the response'
    return format_chunks(chunks)


# mcp.resource("resource://{query}")(get_chunks)
mcp.tool()(get_chunks)


if __name__ == "__main__":
    mcp.run(transport="stdio")
