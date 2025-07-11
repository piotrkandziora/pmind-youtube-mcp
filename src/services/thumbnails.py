"""Thumbnail-related MCP tools implementing YouTube Thumbnails API v3"""

from typing import Dict, Any, Annotated
from pydantic import Field
from fastmcp import FastMCP
from ..config import Config
from ..utils import YouTubeClient, YouTubeAPIError


def register_tools(mcp: FastMCP, config: Config, youtube_client: YouTubeClient):
    """Register thumbnail-related tools with the MCP server"""
    
    @mcp.tool
    async def thumbnails_set(
        video_id: Annotated[str, Field(
            description="The YouTube video ID"
        )],
        image_path: Annotated[str, Field(
            description="Path to the thumbnail image file (JPEG or PNG, max 2MB)"
        )]
    ) -> Dict[str, Any]:
        """
        Upload and set a custom thumbnail for a video.
        
        Requirements:
        - Your channel must be verified
        - Image must be JPEG or PNG format
        - Maximum file size: 2MB
        - Recommended resolution: 1280x720
        - Minimum width: 640 pixels
        - Aspect ratio: 16:9 is ideal
        
        Requires OAuth authentication and video ownership.
        """
        try:
            # Note: The actual file upload implementation would require
            # handling multipart/form-data which is complex in the current setup.
            # This would typically be done through the googleapiclient's MediaFileUpload
            
            response = await youtube_client.thumbnails_set(
                video_id=video_id,
                image_path=image_path
            )
            
            return {
                "success": True,
                "videoId": video_id,
                "thumbnail": response,
                "message": "Thumbnail uploaded and set successfully"
            }
            
        except YouTubeAPIError as e:
            # Common errors:
            # - Channel not verified
            # - Invalid image format or size
            # - Video not owned by authenticated user
            return {
                "error": str(e),
                "details": e.details
            }
        except Exception as e:
            return {
                "error": f"Unexpected error: {str(e)}"
            }