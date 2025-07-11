"""ChannelBanner-related MCP tools implementing YouTube ChannelBanners API v3"""

from typing import Dict, Any, Annotated
from pydantic import Field
from fastmcp import FastMCP
from ..config import Config
from ..utils import YouTubeClient, YouTubeAPIError


def register_tools(mcp: FastMCP, config: Config, youtube_client: YouTubeClient):
    """Register channel banner-related tools with the MCP server"""
    
    @mcp.tool
    async def channel_banners_insert(
        image_path: Annotated[str, Field(
            description="Path to the banner image file (must be 16:9 aspect ratio, min 2048x1152)"
        )]
    ) -> Dict[str, Any]:
        """
        Upload a channel banner image to YouTube.
        
        This is the first step in updating a channel's banner. After upload:
        1. Extract the URL from the response
        2. Use channels_update to set the banner
        
        Image requirements:
        - 16:9 aspect ratio
        - Minimum size: 2048x1152 pixels
        - Recommended: 2560x1440 pixels
        
        Requires OAuth authentication and channel ownership.
        """
        try:
            # Note: The actual file upload implementation would require
            # handling multipart/form-data which is complex in the current setup.
            # This would typically be done through the googleapiclient's MediaFileUpload
            
            response = await youtube_client.channel_banners_insert(image_path=image_path)
            
            return {
                "success": True,
                "url": response.get("url"),
                "message": "Banner uploaded successfully. Use the URL with channels_update to set as channel banner."
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