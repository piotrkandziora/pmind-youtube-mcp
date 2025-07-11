"""PlaylistImages-related MCP tools implementing YouTube PlaylistImages API v3"""

from typing import Dict, Any, Annotated, Optional, List, Union
from pydantic import Field
from fastmcp import FastMCP
from ..config import Config
from ..utils import YouTubeClient, YouTubeAPIError, parse_bool_param, parse_int_param


def register_tools(mcp: FastMCP, config: Config, youtube_client: YouTubeClient):
    """Register playlist images-related tools with the MCP server"""
    
    @mcp.tool
    async def playlist_images_list(
        playlist_id: Annotated[str, Field(
            description="ID of the playlist to retrieve images for"
        )],
        max_results: Annotated[Optional[Union[int, str]], Field(
            description="Maximum number of items to return (1-50, default: 5)"
        )] = 5,
        page_token: Annotated[Optional[str], Field(
            description="Token for pagination"
        )] = None
    ) -> Dict[str, Any]:
        """
        Returns a collection of playlist images that match the API request parameters.
        
        Retrieves thumbnail images associated with a playlist.
        
        Requires OAuth authentication.
        """
        try:
            # Parse integer parameters
            max_results_int = parse_int_param(max_results, default=5)
            
            params = {
                "playlistId": playlist_id,
                "maxResults": max_results_int
            }
            
            if page_token:
                params["pageToken"] = page_token
            
            response = await youtube_client.playlist_images_list(**params)
            
            return {
                "success": True,
                "items": response.get("items", []),
                "pageInfo": response.get("pageInfo", {}),
                "nextPageToken": response.get("nextPageToken"),
                "prevPageToken": response.get("prevPageToken")
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
    async def playlist_images_insert(
        playlist_id: Annotated[str, Field(
            description="ID of the playlist to add image to"
        )],
        image_path: Annotated[str, Field(
            description="Path to the thumbnail image file"
        )]
    ) -> Dict[str, Any]:
        """
        Adds a thumbnail image to a playlist.
        
        Uploads a custom thumbnail image for a playlist.
        
        Image requirements:
        - Max file size: 2MB
        - Supported formats: JPG, GIF, PNG
        - Recommended size: 1280x720 (16:9 aspect ratio)
        
        Requires OAuth authentication and playlist ownership.
        """
        try:
            response = await youtube_client.playlist_images_insert(
                playlist_id=playlist_id,
                image_path=image_path
            )
            
            return {
                "success": True,
                "image": response,
                "message": "Playlist thumbnail uploaded successfully"
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
    async def playlist_images_update(
        playlist_id: Annotated[str, Field(
            description="ID of the playlist to update image for"
        )],
        image_path: Annotated[str, Field(
            description="Path to the new thumbnail image file"
        )]
    ) -> Dict[str, Any]:
        """
        Updates the thumbnail image for an existing playlist.
        
        Replaces the current thumbnail with a new image.
        
        Image requirements:
        - Max file size: 2MB
        - Supported formats: JPG, GIF, PNG
        - Recommended size: 1280x720 (16:9 aspect ratio)
        
        Requires OAuth authentication and playlist ownership.
        """
        try:
            response = await youtube_client.playlist_images_update(
                playlist_id=playlist_id,
                image_path=image_path
            )
            
            return {
                "success": True,
                "image": response,
                "message": "Playlist thumbnail updated successfully"
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
    async def playlist_images_delete(
        playlist_id: Annotated[str, Field(
            description="ID of the playlist to delete image from"
        )]
    ) -> Dict[str, Any]:
        """
        Deletes a playlist thumbnail image.
        
        Removes the custom thumbnail from a playlist, reverting to 
        auto-generated thumbnails.
        
        Requires OAuth authentication and playlist ownership.
        """
        try:
            await youtube_client.playlist_images_delete(playlist_id=playlist_id)
            
            return {
                "success": True,
                "message": "Playlist thumbnail deleted successfully"
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