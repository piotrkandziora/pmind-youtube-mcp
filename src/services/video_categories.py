"""VideoCategory-related MCP tools implementing YouTube VideoCategories API v3"""

from typing import List, Optional, Dict, Any, Annotated, Union
from pydantic import Field
from fastmcp import FastMCP
from ..config import Config
from ..utils import YouTubeClient, YouTubeAPIError, parse_bool_param, parse_int_param


def register_tools(mcp: FastMCP, config: Config, youtube_client: YouTubeClient):
    """Register video category-related tools with the MCP server"""
    
    @mcp.tool
    async def video_categories_list(
        part: Annotated[List[str], Field(
            default=["snippet"],
            description="Category resource properties to include (snippet)"
        )] = ["snippet"],
        region_code: Annotated[Optional[str], Field(
            default=None,
            description="ISO 3166-1 alpha-2 country code (e.g., 'US', 'GB')"
        )] = None,
        hl: Annotated[Optional[str], Field(
            default=None,
            description="Language for text values (ISO 639-1 two-letter code)"
        )] = None,
        id: Annotated[Optional[str], Field(
            default=None,
            description="Comma-separated list of video category IDs"
        )] = None
    ) -> Dict[str, Any]:
        """
        List categories that can be associated with YouTube videos.
        
        Returns video categories available in the specified region.
        Categories that are assignable can be used when uploading or updating videos.
        
        Must specify either region_code or id parameter.
        """
        try:
            # Validate that at least one filter is provided
            if not region_code and not id:
                return {
                    "error": "Must specify either region_code or id parameter"
                }
            
            # Build request parameters
            params = {
                "part": ",".join(part)
            }
            
            # Add filter parameters
            if region_code:
                params["regionCode"] = region_code
            if id:
                params["id"] = id
                
            # Add optional parameters
            if hl:
                params["hl"] = hl
            
            # Make the API call
            response = await youtube_client.video_categories_list(**params)
            
            # Format the response
            categories = []
            for item in response.get("items", []):
                category = {
                    "id": item["id"],
                    "title": item["snippet"]["title"],
                    "channelId": item["snippet"]["channelId"],
                    "assignable": item["snippet"].get("assignable", False)
                }
                categories.append(category)
            
            return {
                "items": response.get("items", []),
                "categories": categories,
                "totalResults": len(categories),
                "regionCode": region_code
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