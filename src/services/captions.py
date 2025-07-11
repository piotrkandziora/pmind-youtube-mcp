"""Caption-related MCP tools implementing YouTube Captions API v3"""

from typing import List, Optional, Dict, Any, Literal, Annotated, Union
from pydantic import Field
from fastmcp import FastMCP
from ..config import Config
from ..utils import YouTubeClient, YouTubeAPIError, parse_bool_param, parse_int_param


def register_tools(mcp: FastMCP, config: Config, youtube_client: YouTubeClient):
    """Register caption-related tools with the MCP server"""
    
    @mcp.tool
    async def captions_list(
        video_id: Annotated[str, Field(
            description="The YouTube video ID"
        )],
        part: Annotated[List[str], Field(
            default=["id", "snippet"],
            description="Caption resource properties to include"
        )] = ["id", "snippet"]
    ) -> Dict[str, Any]:
        """
        List caption tracks for a video.
        
        Returns information about available captions but not the actual caption content.
        Use captions_download to retrieve caption content.
        """
        try:
            params = {
                "part": ",".join(part),
                "videoId": video_id
            }
            
            response = await youtube_client.captions_list(**params)
            
            return {
                "videoId": video_id,
                "captionCount": len(response.get("items", [])),
                "items": response.get("items", [])
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
    
    @mcp.tool
    async def captions_download(
        id: Annotated[str, Field(
            description="The caption track ID"
        )],
        tfmt: Annotated[Optional[Literal["srt", "sbv", "vtt", "ttml"]], Field(
            default=None,
            description="Output format for the caption track"
        )] = None,
        tlang: Annotated[Optional[str], Field(
            default=None,
            description="Target language for translation (ISO 639-1 code)"
        )] = None
    ) -> Dict[str, Any]:
        """
        Download a caption track.
        
        Can optionally specify format and translate to another language.
        """
        try:
            params = {"id": id}
            
            if tfmt:
                params["tfmt"] = tfmt
            if tlang:
                params["tlang"] = tlang
            
            response = await youtube_client.captions_download(**params)
            
            return {
                "captionId": id,
                "format": tfmt or "original",
                "language": tlang or "original",
                "content": response
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
    
    @mcp.tool
    async def captions_update(
        id: Annotated[str, Field(
            description="The caption track ID to update"
        )],
        is_draft: Annotated[bool, Field(
            default=False,
            description="Whether the caption track is a draft"
        )] = False,
        track_name: Annotated[Optional[str], Field(
            default=None,
            description="Caption track name"
        )] = None,
        track_language: Annotated[Optional[str], Field(
            default=None,
            description="Caption track language (ISO 639-1 code)"
        )] = None
    ) -> Dict[str, Any]:
        """
        Update caption track metadata.
        
        Can update draft status and track metadata.
        Requires OAuth authentication and ownership of the video.
        """
        try:
            # Build update body
            body = {"id": id}
            parts = ["id"]
            
            if any([is_draft, track_name is not None, track_language is not None]):
                snippet = {}
                
                if is_draft:
                    snippet["isDraft"] = is_draft
                if track_name is not None:
                    snippet["name"] = track_name
                if track_language is not None:
                    snippet["language"] = track_language
                    
                body["snippet"] = snippet
                parts.append("snippet")
            else:
                return {
                    "error": "At least one field must be specified for update"
                }
            
            response = await youtube_client.captions_update(
                part=",".join(parts),
                body=body
            )
            
            return {
                "success": True,
                "caption": response,
                "message": "Caption track updated successfully"
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
    
    @mcp.tool
    async def captions_delete(
        id: Annotated[str, Field(
            description="The caption track ID to delete"
        )]
    ) -> Dict[str, Any]:
        """
        Delete a caption track.
        
        Requires OAuth authentication and ownership of the video.
        This action cannot be undone.
        """
        try:
            await youtube_client.captions_delete(id=id)
            
            return {
                "success": True,
                "captionId": id,
                "message": "Caption track deleted successfully"
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