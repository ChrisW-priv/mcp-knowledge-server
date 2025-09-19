from typing import Any
import httpx
from httpx import HTTPStatusError
from mcp.server.fastmcp import FastMCP
from urllib.parse import urljoin
import os
import logging
import sys

logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("knowledge", log_level="INFO")


TOKEN = os.getenv("KNOWLEDGE_USER_TOKEN")
URL_BASE = os.getenv("KNOWLEDGE_URL_BASE")


async def make_get_chunks_request(query: str) -> dict[str, Any] | None:
    """
    Make a request to the knowledge API
    """

    url = urljoin(URL_BASE, "/get-chunks/")
    options = {
        "url": url,
        "headers": {"Authorization": f"Token {TOKEN}"},
        "data": {"query": query},
        "timeout": 30.0,
    }
    logger.debug(f"Making request to {url} with {options=}")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(**options)
            response.raise_for_status()
            return response.json()
        except HTTPStatusError:
            logger.error(
                f"Failed to retrieve data from the knowledge API: {response.status_code=}, {response.text=}"
            )
            return None
        except Exception as e:
            logger.exception(e)
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
    env_unset = False
    if TOKEN is None:
        logger.error(
            "No token provided! Is there an MCP config that passes the KNOWLEDGE_USER_TOKEN variable? MCP blocks all environment variables by default."
        )
        env_unset = True
    if URL_BASE is None:
        logger.error(
            "No URL provided! Is there an MCP config that passes the KNOWLEDGE_URL_BASE variable? MCP blocks all environment variables by default."
        )
        env_unset = True
    if env_unset:
        sys.exit(1)
    logger.info("Starting knowledge server...")
    mcp.run(transport="stdio")
