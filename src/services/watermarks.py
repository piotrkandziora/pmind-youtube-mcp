"""Watermark-related MCP tools implementing YouTube Watermarks API v3"""

from typing import Optional, Dict, Any, Annotated, Literal, Union
from pydantic import Field
from fastmcp import FastMCP
from ..config import Config
from ..utils import YouTubeClient, YouTubeAPIError, parse_bool_param, parse_int_param


def register_tools(mcp: FastMCP, config: Config, youtube_client: YouTubeClient):
    """Register watermark-related tools with the MCP server"""
    
    @mcp.tool
    async def watermarks_set(
        channel_id: Annotated[str, Field(
            description="The YouTube channel ID"
        )],
        image_path: Annotated[str, Field(
            description="Path to the watermark image file (PNG, GIF, or BMP format, max 1MB)"
        )],
        position: Annotated[Literal["bottomLeft", "bottomRight", "topLeft", "topRight"], Field(
            default="bottomRight",
            description="Position of the watermark on the video"
        )] = "bottomRight",
        offset_ms: Annotated[Optional[Union[int, str]], Field(
            default=None,
            description="Offset from the start of the video when the watermark should appear (milliseconds)"
        )] = None,
        duration_ms: Annotated[Optional[Union[int, str]], Field(
            default=None,
            description="Duration for which the watermark should be displayed (milliseconds)"
        )] = None
    ) -> Dict[str, Any]:
        """
        Upload and set a watermark image for a channel.
        
        Requirements:
        - Channel must be owned by authenticated user
        - Image must be PNG, GIF, or BMP format
        - Maximum file size: 1MB
        - Recommended size: 150x150 pixels
        - Transparency is supported for PNG files
        
        Timing options:
        - offset_ms: When to start showing (default: 0)
        - duration_ms: How long to show (default: entire video)
        
        Requires OAuth authentication and channel ownership.
        """
        try:
            # Parse integer parameters
            offset_ms_int = parse_int_param(offset_ms)
            duration_ms_int = parse_int_param(duration_ms)
            
            # Note: The actual file upload implementation would require
            # handling multipart/form-data which is complex in the current setup.
            # This would typically be done through the googleapiclient's MediaFileUpload
            
            timing = {}
            if offset_ms_int is not None:
                timing["offsetMs"] = offset_ms_int
            if duration_ms_int is not None:
                timing["durationMs"] = duration_ms_int
            
            response = await youtube_client.watermarks_set(
                channel_id=channel_id,
                image_path=image_path,
                position=position,
                timing=timing
            )
            
            return {
                "success": True,
                "channelId": channel_id,
                "watermark": response,
                "message": "Watermark uploaded and set successfully"
            }
            
        except YouTubeAPIError as e:
            # Common errors:
            # - Channel not owned by authenticated user
            # - Invalid image format or size
            # - Invalid timing parameters
            return {
                "error": str(e),
                "details": e.details
            }
        except Exception as e:
            return {
                "error": f"Unexpected error: {str(e)}"
            }
    
    @mcp.tool
    async def watermarks_unset(
        channel_id: Annotated[str, Field(
            description="The YouTube channel ID"
        )]
    ) -> Dict[str, Any]:
        """
        Remove the watermark image from a channel.
        
        Permanently removes the watermark from all videos on the channel.
        
        Requires OAuth authentication and channel ownership.
        """
        try:
            await youtube_client.watermarks_unset(channel_id=channel_id)
            
            return {
                "success": True,
                "channelId": channel_id,
                "message": "Watermark removed successfully"
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