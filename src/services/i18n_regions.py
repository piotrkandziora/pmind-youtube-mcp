"""i18nRegion-related MCP tools implementing YouTube i18nRegions API v3"""

from typing import List, Optional, Dict, Any, Annotated, Union
from pydantic import Field
from fastmcp import FastMCP
from ..config import Config
from ..utils import YouTubeClient, YouTubeAPIError, parse_bool_param, parse_int_param


def register_tools(mcp: FastMCP, config: Config, youtube_client: YouTubeClient):
    """Register i18n region-related tools with the MCP server"""
    
    @mcp.tool
    async def i18n_regions_list(
        part: Annotated[List[str], Field(
            default=["snippet"],
            description="Region resource properties to include (snippet)"
        )] = ["snippet"],
        hl: Annotated[Optional[str], Field(
            default=None,
            description="Language for text values (ISO 639-1 two-letter code)"
        )] = None
    ) -> Dict[str, Any]:
        """
        List content regions that the YouTube website supports.
        
        Returns a list of geographic regions where YouTube is available.
        The region codes can be used as regionCode parameter in other API methods
        like search.list, videos.list, etc.
        
        Each region includes:
        - id: The region code (ISO 3166-1 alpha-2)
        - name: The localized name of the region
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
            response = await youtube_client.i18n_regions_list(**params)
            
            # Format the response
            regions = []
            for item in response.get("items", []):
                region = {
                    "id": item["id"],
                    "name": item["snippet"]["name"]
                }
                regions.append(region)
            
            return {
                "items": response.get("items", []),
                "regions": regions,
                "totalResults": len(regions),
                "language": hl if hl else "default"
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