"""PlaylistItems-related MCP tools implementing YouTube PlaylistItems API v3"""

from typing import Dict, Any, Annotated, Optional, List, Union
from pydantic import Field
from fastmcp import FastMCP
from ..config import Config
from ..utils import YouTubeClient, YouTubeAPIError, parse_bool_param, parse_int_param


def register_tools(mcp: FastMCP, config: Config, youtube_client: YouTubeClient):
    """Register playlist items-related tools with the MCP server"""
    
    @mcp.tool
    async def playlist_items_list(
        part: Annotated[List[str], Field(
            description="Comma-separated list of resource properties to include",
            default=["snippet", "contentDetails", "status"]
        )] = None,
        playlist_id: Annotated[Optional[str], Field(
            description="ID of the playlist to retrieve items from"
        )] = None,
        id: Annotated[Optional[List[str]], Field(
            description="List of playlist item IDs to retrieve"
        )] = None,
        max_results: Annotated[Optional[Union[int, str]], Field(
            description="Maximum number of items to return (1-50, default: 5)"
        )] = 5,
        page_token: Annotated[Optional[str], Field(
            description="Token for pagination"
        )] = None,
        video_id: Annotated[Optional[str], Field(
            description="Filter by video ID"
        )] = None
    ) -> Dict[str, Any]:
        """
        Returns a collection of playlist items that match the API request parameters.
        
        You can retrieve all playlist items in a specified playlist or retrieve 
        one or more playlist items by their unique IDs.
        
        Either playlist_id or id parameter is required.
        
        Requires OAuth authentication for private playlists.
        """
        try:
            # Parse integer parameters
            max_results_int = parse_int_param(max_results, default=5)
            
            if not playlist_id and not id:
                return {
                    "error": "Either playlist_id or id parameter is required"
                }
            
            if part is None:
                part = ["snippet", "contentDetails", "status"]
            
            params = {
                "part": ",".join(part),
                "maxResults": max_results_int
            }
            
            if playlist_id:
                params["playlistId"] = playlist_id
            if id:
                params["id"] = ",".join(id) if isinstance(id, list) else id
            if page_token:
                params["pageToken"] = page_token
            if video_id:
                params["videoId"] = video_id
            
            response = await youtube_client.playlist_items_list(**params)
            
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
    async def playlist_items_insert(
        playlist_id: Annotated[str, Field(
            description="ID of the playlist to add item to"
        )],
        video_id: Annotated[str, Field(
            description="ID of the video to add to playlist"
        )],
        position: Annotated[Optional[Union[int, str]], Field(
            description="Position in playlist (0-based index)"
        )] = None,
        note: Annotated[Optional[str], Field(
            description="Note about the playlist item"
        )] = None,
        start_at: Annotated[Optional[str], Field(
            description="Time offset to start playback (e.g., '00:00:15')"
        )] = None,
        end_at: Annotated[Optional[str], Field(
            description="Time offset to end playback (e.g., '00:05:30')"
        )] = None
    ) -> Dict[str, Any]:
        """
        Adds a resource to a playlist.
        
        Adds a video to a playlist. You can add a video to your own playlist 
        or to a playlist that you're allowed to contribute to.
        
        Requires OAuth authentication and appropriate permissions.
        """
        try:
            # Parse integer parameters
            position_int = parse_int_param(position)
            
            body = {
                "snippet": {
                    "playlistId": playlist_id,
                    "resourceId": {
                        "kind": "youtube#video",
                        "videoId": video_id
                    }
                }
            }
            
            if position_int is not None:
                body["snippet"]["position"] = position_int
            
            if note:
                body["contentDetails"] = {"note": note}
            
            if start_at or end_at:
                if "contentDetails" not in body:
                    body["contentDetails"] = {}
                if start_at:
                    body["contentDetails"]["startAt"] = start_at
                if end_at:
                    body["contentDetails"]["endAt"] = end_at
            
            response = await youtube_client.playlist_items_insert(
                part="snippet,contentDetails",
                body=body
            )
            
            return {
                "success": True,
                "playlistItem": response,
                "message": f"Video {video_id} added to playlist {playlist_id}"
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
    async def playlist_items_update(
        playlist_item_id: Annotated[str, Field(
            description="ID of the playlist item to update"
        )],
        playlist_id: Annotated[str, Field(
            description="ID of the playlist containing the item"
        )],
        video_id: Annotated[str, Field(
            description="ID of the video"
        )],
        position: Annotated[Optional[Union[int, str]], Field(
            description="New position in playlist (0-based index)"
        )] = None,
        note: Annotated[Optional[str], Field(
            description="Note about the playlist item"
        )] = None,
        start_at: Annotated[Optional[str], Field(
            description="Time offset to start playback (e.g., '00:00:15')"
        )] = None,
        end_at: Annotated[Optional[str], Field(
            description="Time offset to end playback (e.g., '00:05:30')"
        )] = None
    ) -> Dict[str, Any]:
        """
        Modifies a playlist item.
        
        Updates an existing playlist item. For example, you could update the 
        item's position in the playlist.
        
        Requires OAuth authentication and playlist ownership.
        """
        try:
            # Parse integer parameters
            position_int = parse_int_param(position)
            
            body = {
                "id": playlist_item_id,
                "snippet": {
                    "playlistId": playlist_id,
                    "resourceId": {
                        "kind": "youtube#video",
                        "videoId": video_id
                    }
                }
            }
            
            if position_int is not None:
                body["snippet"]["position"] = position_int
            
            if note is not None:
                body["contentDetails"] = {"note": note}
            
            if start_at or end_at:
                if "contentDetails" not in body:
                    body["contentDetails"] = {}
                if start_at:
                    body["contentDetails"]["startAt"] = start_at
                if end_at:
                    body["contentDetails"]["endAt"] = end_at
            
            response = await youtube_client.playlist_items_update(
                part="snippet,contentDetails",
                body=body
            )
            
            return {
                "success": True,
                "playlistItem": response,
                "message": "Playlist item updated successfully"
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
    async def playlist_items_delete(
        playlist_item_id: Annotated[str, Field(
            description="ID of the playlist item to delete"
        )]
    ) -> Dict[str, Any]:
        """
        Deletes a playlist item.
        
        Removes an item from a playlist.
        
        Requires OAuth authentication and playlist ownership.
        """
        try:
            await youtube_client.playlist_items_delete(id=playlist_item_id)
            
            return {
                "success": True,
                "message": f"Playlist item {playlist_item_id} deleted successfully"
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