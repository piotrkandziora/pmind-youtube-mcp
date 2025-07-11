"""MembershipsLevel-related MCP tools implementing YouTube MembershipsLevels API v3"""

from typing import List, Dict, Any, Annotated
from pydantic import Field
from fastmcp import FastMCP
from ..config import Config
from ..utils import YouTubeClient, YouTubeAPIError


def register_tools(mcp: FastMCP, config: Config, youtube_client: YouTubeClient):
    """Register memberships level-related tools with the MCP server"""
    
    @mcp.tool
    async def memberships_levels_list(
        part: Annotated[List[str], Field(
            default=["id", "snippet"],
            description="MembershipsLevel resource properties to include"
        )] = ["id", "snippet"]
    ) -> Dict[str, Any]:
        """
        List membership levels for your channel.
        
        Requires OAuth authentication by the channel owner.
        Only available for channels with memberships enabled.
        Note: Access to this API requires approval from YouTube.
        Contact your YouTube representative for access.
        """
        try:
            # Build request parameters
            params = {
                "part": ",".join(part)
            }
            
            # Make the API call
            response = await youtube_client.memberships_levels_list(**params)
            
            return {
                "items": response.get("items", []),
                "levelCount": len(response.get("items", [])),
                "levels": [
                    {
                        "id": item.get("id"),
                        "displayName": item.get("snippet", {}).get("levelDetails", {}).get("displayName"),
                        "creatorChannelId": item.get("snippet", {}).get("creatorChannelId")
                    }
                    for item in response.get("items", [])
                ]
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