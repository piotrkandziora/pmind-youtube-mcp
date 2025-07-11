"""i18nLanguage-related MCP tools implementing YouTube i18nLanguages API v3"""

from typing import List, Optional, Dict, Any, Annotated, Union
from pydantic import Field
from fastmcp import FastMCP
from ..config import Config
from ..utils import YouTubeClient, YouTubeAPIError, parse_bool_param, parse_int_param


def register_tools(mcp: FastMCP, config: Config, youtube_client: YouTubeClient):
    """Register i18n language-related tools with the MCP server"""
    
    @mcp.tool
    async def i18n_languages_list(
        part: Annotated[List[str], Field(
            default=["snippet"],
            description="Language resource properties to include (snippet)"
        )] = ["snippet"],
        hl: Annotated[Optional[str], Field(
            default=None,
            description="Language for text values (ISO 639-1 two-letter code)"
        )] = None
    ) -> Dict[str, Any]:
        """
        List application languages that the YouTube website supports.
        
        Returns a list of languages that YouTube supports for its user interface.
        The language codes (BCP-47) can be used as hl parameter in other API methods
        to retrieve localized information.
        
        Each language includes:
        - id: The BCP-47 language code
        - name: The localized name of the language
        """
        try:
            # Build request parameters
            params = {
                "part": ",".join(part)
            }
            
            # Add optional parameters
            if hl:
                params["hl"] = hl
            
            # Make the API call
            response = await youtube_client.i18n_languages_list(**params)
            
            # Format the response
            languages = []
            for item in response.get("items", []):
                language = {
                    "id": item["id"],
                    "name": item["snippet"]["name"]
                }
                languages.append(language)
            
            return {
                "items": response.get("items", []),
                "languages": languages,
                "totalResults": len(languages),
                "displayLanguage": hl if hl else "default"
            }
            
        except YouTubeAPIError as e:
            return {
                "error": str(e),
                "details": e.details
            }
        except Exception as e:
            return {
                "error": f"Unexpected error: {str(e)}"
            }