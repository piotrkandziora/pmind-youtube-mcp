"""Playlists-related MCP tools implementing YouTube Playlists API v3"""

from typing import Dict, Any, Annotated, Optional, List, Union
from pydantic import Field
from fastmcp import FastMCP
from ..config import Config
from ..utils import YouTubeClient, YouTubeAPIError, parse_bool_param, parse_int_param


def register_tools(mcp: FastMCP, config: Config, youtube_client: YouTubeClient):
    """Register playlists-related tools with the MCP server"""
    
    @mcp.tool
    async def playlists_list(
        part: Annotated[List[str], Field(
            description="Comma-separated list of resource properties to include",
            default=["snippet", "status", "contentDetails"]
        )] = None,
        channel_id: Annotated[Optional[str], Field(
            description="Filter by channel ID"
        )] = None,
        id: Annotated[Optional[List[str]], Field(
            description="List of playlist IDs to retrieve"
        )] = None,
        mine: Annotated[bool, Field(
            default=False,
            description="Return playlists owned by authenticated user"
        )] = False,
        max_results: Annotated[Optional[Union[int, str]], Field(
            description="Maximum number of items to return (1-50, default: 5)"
        )] = 5,
        page_token: Annotated[Optional[str], Field(
            description="Token for pagination"
        )] = None
    ) -> Dict[str, Any]:
        """
        Returns a collection of playlists that match the API request parameters.
        
        You can retrieve all playlists associated with a particular channel, 
        including your own, or retrieve one or more playlists by their unique IDs.
        
        Requires OAuth authentication for 'mine' parameter.
        """
        try:
            # Parse integer parameters
            max_results_int = parse_int_param(max_results, default=5)
            
            if not channel_id and not id and not mine:
                return {
                    "error": "One of channel_id, id, or mine parameter is required"
                }
            
            if part is None:
                part = ["snippet", "status", "contentDetails"]
            
            params = {
                "part": ",".join(part),
                "maxResults": max_results_int
            }
            
            if channel_id:
                params["channelId"] = channel_id
            if id:
                params["id"] = ",".join(id) if isinstance(id, list) else id
            if mine:
                params["mine"] = mine
            if page_token:
                params["pageToken"] = page_token
            
            response = await youtube_client.playlists_list(**params)
            
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
    async def playlists_insert(
        title: Annotated[str, Field(
            description="Title for the playlist"
        )],
        description: Annotated[Optional[str], Field(
            description="Description of the playlist"
        )] = None,
        privacy_status: Annotated[Optional[str], Field(
            description="Privacy status: private, public, or unlisted",
            pattern="^(private|public|unlisted)$"
        )] = "private",
        tags: Annotated[Optional[List[str]], Field(
            description="Tags associated with the playlist"
        )] = None,
        default_language: Annotated[Optional[str], Field(
            description="Default language of playlist's textual metadata"
        )] = None
    ) -> Dict[str, Any]:
        """
        Creates a playlist.
        
        Creates a new playlist on the authenticated user's channel.
        
        Requires OAuth authentication.
        """
        try:
            body = {
                "snippet": {
                    "title": title
                },
                "status": {
                    "privacyStatus": privacy_status
                }
            }
            
            if description:
                body["snippet"]["description"] = description
            if tags:
                body["snippet"]["tags"] = tags
            if default_language:
                body["snippet"]["defaultLanguage"] = default_language
            
            response = await youtube_client.playlists_insert(
                part="snippet,status",
                body=body
            )
            
            return {
                "success": True,
                "playlist": response,
                "message": f"Playlist '{title}' created successfully"
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
    async def playlists_update(
        playlist_id: Annotated[str, Field(
            description="ID of the playlist to update"
        )],
        title: Annotated[Optional[str], Field(
            description="New title for the playlist"
        )] = None,
        description: Annotated[Optional[str], Field(
            description="New description for the playlist"
        )] = None,
        privacy_status: Annotated[Optional[str], Field(
            description="New privacy status: private, public, or unlisted",
            pattern="^(private|public|unlisted)$"
        )] = None,
        tags: Annotated[Optional[List[str]], Field(
            description="New tags for the playlist"
        )] = None,
        default_language: Annotated[Optional[str], Field(
            description="Default language of playlist's textual metadata"
        )] = None
    ) -> Dict[str, Any]:
        """
        Modifies a playlist.
        
        Updates an existing playlist's metadata. You must provide at least 
        one field to update.
        
        Requires OAuth authentication and playlist ownership.
        """
        try:
            # First get the current playlist to preserve existing values
            current = await youtube_client.playlists_list(
                part="snippet,status",
                id=playlist_id
            )
            
            if not current.get("items"):
                return {
                    "error": f"Playlist with ID '{playlist_id}' not found"
                }
            
            current_item = current["items"][0]
            
            body = {
                "id": playlist_id,
                "snippet": {
                    "title": title or current_item["snippet"]["title"]
                }
            }
            
            # Update snippet fields
            if description is not None:
                body["snippet"]["description"] = description
            elif "description" in current_item["snippet"]:
                body["snippet"]["description"] = current_item["snippet"]["description"]
            
            if tags is not None:
                body["snippet"]["tags"] = tags
            elif "tags" in current_item["snippet"]:
                body["snippet"]["tags"] = current_item["snippet"]["tags"]
            
            if default_language is not None:
                body["snippet"]["defaultLanguage"] = default_language
            elif "defaultLanguage" in current_item["snippet"]:
                body["snippet"]["defaultLanguage"] = current_item["snippet"]["defaultLanguage"]
            
            # Update status if provided
            if privacy_status is not None:
                body["status"] = {"privacyStatus": privacy_status}
            
            response = await youtube_client.playlists_update(
                part="snippet,status",
                body=body
            )
            
            return {
                "success": True,
                "playlist": response,
                "message": "Playlist updated successfully"
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
    async def playlists_delete(
        playlist_id: Annotated[str, Field(
            description="ID of the playlist to delete"
        )]
    ) -> Dict[str, Any]:
        """
        Deletes a playlist.
        
        Permanently deletes a playlist. This action cannot be undone.
        
        Requires OAuth authentication and playlist ownership.
        """
        try:
            await youtube_client.playlists_delete(id=playlist_id)
            
            return {
                "success": True,
                "message": f"Playlist {playlist_id} deleted successfully"
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
    
    # Keep the legacy method for backward compatibility but mark as deprecated
    @mcp.tool
    async def playlists_get_playlist(
        playlist_id: Annotated[str, Field(description="The YouTube playlist ID")]
    ) -> Dict[str, Any]:
        """
        [DEPRECATED] Get information about a YouTube playlist.
        
        This method is deprecated. Use playlists_list with id parameter instead.
        """
        try:
            response = await youtube_client.playlists_list(
                part="snippet,status,contentDetails",
                id=playlist_id
            )
            
            if not response.get("items"):
                return {
                    "error": f"Playlist with ID '{playlist_id}' not found"
                }
            
            playlist = response["items"][0]
            
            # Format response to match legacy format
            return {
                "id": playlist["id"],
                "title": playlist["snippet"]["title"],
                "description": playlist["snippet"].get("description", ""),
                "channelId": playlist["snippet"]["channelId"],
                "channelTitle": playlist["snippet"]["channelTitle"],
                "publishedAt": playlist["snippet"]["publishedAt"],
                "thumbnails": playlist["snippet"]["thumbnails"],
                "itemCount": playlist["contentDetails"]["itemCount"],
                "privacyStatus": playlist["status"]["privacyStatus"]
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