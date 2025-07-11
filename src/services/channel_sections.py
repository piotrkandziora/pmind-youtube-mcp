"""ChannelSection-related MCP tools implementing YouTube ChannelSections API v3"""

from typing import List, Optional, Dict, Any, Literal, Annotated, Union
from pydantic import Field
from fastmcp import FastMCP
from ..config import Config
from ..utils import YouTubeClient, YouTubeAPIError, parse_bool_param, parse_int_param


def register_tools(mcp: FastMCP, config: Config, youtube_client: YouTubeClient):
    """Register channel section-related tools with the MCP server"""
    
    @mcp.tool
    async def channel_sections_list(
        part: Annotated[List[str], Field(
            description="ChannelSection resource properties to include (snippet, contentDetails, etc.)"
        )],
        channel_id: Annotated[Optional[str], Field(
            default=None,
            description="Channel ID to get sections for"
        )] = None,
        mine: Annotated[bool, Field(
            default=False,
            description="Return sections for authenticated user's channel"
        )] = False,
        hl: Annotated[Optional[str], Field(
            default=None,
            description="Language for localized properties (ISO 639-1 code)"
        )] = None,
        id: Annotated[Optional[str], Field(
            default=None,
            description="Comma-separated list of section IDs"
        )] = None
    ) -> Dict[str, Any]:
        """
        List channel sections that match the request criteria.
        
        Must specify either channel_id, mine=True, or id parameter.
        """
        try:
            # Validate that at least one filter is provided
            if not any([channel_id, mine, id]):
                return {
                    "error": "Must specify either channel_id, mine=True, or id parameter"
                }
            
            # Build request parameters
            params = {
                "part": ",".join(part)
            }
            
            # Add filter parameters
            if channel_id:
                params["channelId"] = channel_id
            if mine:
                params["mine"] = mine
            if id:
                params["id"] = id
                
            # Add optional parameters
            if hl:
                params["hl"] = hl
            
            # Make the API call
            response = await youtube_client.channel_sections_list(**params)
            
            return {
                "items": response.get("items", []),
                "itemCount": len(response.get("items", []))
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
    async def channel_sections_insert(
        type: Annotated[Literal[
            "allPlaylists",
            "completedEvents",
            "likedPlaylists",
            "likes",
            "liveEvents",
            "multipleChannels",
            "multiplePlaylists",
            "popularUploads",
            "recentActivity",
            "recentPosts",
            "recentUploads",
            "singlePlaylist",
            "subscriptions",
            "upcomingEvents"
        ], Field(
            description="Type of channel section"
        )],
        style: Annotated[Literal["horizontalRow", "verticalList"], Field(
            description="How the section displays"
        )],
        title: Annotated[Optional[str], Field(
            default=None,
            description="Section title (required for multiplePlaylists/multipleChannels)"
        )] = None,
        position: Annotated[Optional[Union[int, str]], Field(
            default=None,
            description="Section position (0-based)"
        )] = None,
        playlist_ids: Annotated[Optional[List[str]], Field(
            default=None,
            description="Playlist IDs for multiplePlaylists type"
        )] = None,
        channel_ids: Annotated[Optional[List[str]], Field(
            default=None,
            description="Channel IDs for multipleChannels type"
        )] = None,
        playlist_id: Annotated[Optional[str], Field(
            default=None,
            description="Playlist ID for singlePlaylist type"
        )] = None
    ) -> Dict[str, Any]:
        """
        Add a channel section to your channel.
        
        Maximum of 10 sections per channel.
        Requires OAuth authentication and channel ownership.
        """
        try:
            # Parse integer parameters
            position_int = parse_int_param(position)
            
            # Build the request body
            body = {
                "snippet": {
                    "type": type,
                    "style": style
                }
            }
            
            # Add title if provided
            if title:
                body["snippet"]["title"] = title
                
            # Add position if provided
            if position_int is not None:
                body["snippet"]["position"] = position_int
            
            # Add content details based on type
            if type == "multiplePlaylists" and playlist_ids:
                body["contentDetails"] = {
                    "playlists": playlist_ids
                }
            elif type == "multipleChannels" and channel_ids:
                body["contentDetails"] = {
                    "channels": channel_ids
                }
            elif type == "singlePlaylist" and playlist_id:
                body["contentDetails"] = {
                    "playlists": [playlist_id]
                }
            
            # Validate required fields
            if type in ["multiplePlaylists", "multipleChannels"] and not title:
                return {
                    "error": f"Title is required for {type} sections"
                }
            
            response = await youtube_client.channel_sections_insert(
                part="snippet,contentDetails",
                body=body
            )
            
            return {
                "success": True,
                "section": response,
                "message": "Channel section created successfully"
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
    async def channel_sections_update(
        id: Annotated[str, Field(
            description="Channel section ID to update"
        )],
        type: Annotated[Optional[Literal[
            "allPlaylists",
            "completedEvents",
            "likedPlaylists",
            "likes",
            "liveEvents",
            "multipleChannels",
            "multiplePlaylists",
            "popularUploads",
            "recentActivity",
            "recentPosts",
            "recentUploads",
            "singlePlaylist",
            "subscriptions",
            "upcomingEvents"
        ]], Field(
            default=None,
            description="New section type"
        )] = None,
        style: Annotated[Optional[Literal["horizontalRow", "verticalList"]], Field(
            default=None,
            description="New display style"
        )] = None,
        title: Annotated[Optional[str], Field(
            default=None,
            description="New section title"
        )] = None,
        position: Annotated[Optional[Union[int, str]], Field(
            default=None,
            description="New position (0-based)"
        )] = None,
        playlist_ids: Annotated[Optional[List[str]], Field(
            default=None,
            description="New playlist IDs for multiplePlaylists"
        )] = None,
        channel_ids: Annotated[Optional[List[str]], Field(
            default=None,
            description="New channel IDs for multipleChannels"
        )] = None,
        playlist_id: Annotated[Optional[str], Field(
            default=None,
            description="New playlist ID for singlePlaylist"
        )] = None
    ) -> Dict[str, Any]:
        """
        Update a channel section.
        
        Requires OAuth authentication and channel ownership.
        """
        try:
            # Parse integer parameters
            position_int = parse_int_param(position)
            
            # Check if at least one field is being updated
            if not any([type, style, title, position_int is not None, 
                       playlist_ids, channel_ids, playlist_id]):
                return {
                    "error": "At least one field must be specified for update"
                }
            
            # Build update body
            body = {"id": id}
            parts = ["id"]
            
            # Add snippet updates
            if any([type, style, title, position_int is not None]):
                snippet = {}
                if type:
                    snippet["type"] = type
                if style:
                    snippet["style"] = style
                if title is not None:
                    snippet["title"] = title
                if position_int is not None:
                    snippet["position"] = position_int
                    
                body["snippet"] = snippet
                parts.append("snippet")
            
            # Add content details updates
            if any([playlist_ids, channel_ids, playlist_id]):
                content_details = {}
                
                if playlist_ids:
                    content_details["playlists"] = playlist_ids
                elif channel_ids:
                    content_details["channels"] = channel_ids
                elif playlist_id:
                    content_details["playlists"] = [playlist_id]
                    
                body["contentDetails"] = content_details
                parts.append("contentDetails")
            
            response = await youtube_client.channel_sections_update(
                part=",".join(parts),
                body=body
            )
            
            return {
                "success": True,
                "section": response,
                "message": "Channel section updated successfully"
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
    async def channel_sections_delete(
        id: Annotated[str, Field(
            description="Channel section ID to delete"
        )]
    ) -> Dict[str, Any]:
        """
        Delete a channel section.
        
        Requires OAuth authentication and channel ownership.
        This action cannot be undone.
        """
        try:
            await youtube_client.channel_sections_delete(id=id)
            
            return {
                "success": True,
                "sectionId": id,
                "message": "Channel section deleted successfully"
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