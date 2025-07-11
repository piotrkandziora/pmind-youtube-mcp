"""Channel-related MCP tools implementing YouTube Channels API v3"""

from typing import List, Optional, Dict, Any, Literal, Annotated, Union
from pydantic import Field
from fastmcp import FastMCP
from ..config import Config
from ..utils import YouTubeClient, YouTubeAPIError, parse_bool_param, parse_int_param


def register_tools(mcp: FastMCP, config: Config, youtube_client: YouTubeClient):
    """Register channel-related tools with the MCP server"""
    
    @mcp.tool
    async def channels_list(
        part: Annotated[List[str], Field(
            description="Channel resource properties to include (snippet, statistics, brandingSettings, etc.)"
        )],
        for_handle: Annotated[Optional[str], Field(
            default=None,
            description="YouTube handle (e.g., '@youtube')"
        )] = None,
        for_username: Annotated[Optional[str], Field(
            default=None,
            description="YouTube username"
        )] = None,
        id: Annotated[Optional[str], Field(
            default=None,
            description="Comma-separated list of channel IDs"
        )] = None,
        managed_by_me: Annotated[Optional[Union[bool, str]], Field(
            default=None,
            description="Return channels managed by authenticated user (requires OAuth)"
        )] = None,
        mine: Annotated[Optional[Union[bool, str]], Field(
            default=None,
            description="Return channels owned by authenticated user (requires OAuth)"
        )] = None,
        hl: Annotated[Optional[str], Field(
            default=None,
            description="Language for localized properties (ISO 639-1 two-letter code)"
        )] = None,
        max_results: Annotated[Union[int, str], Field(
            default=5,
            description="Maximum number of items to return"
        )] = 5,
        page_token: Annotated[Optional[str], Field(
            default=None,
            description="Token for specific results page"
        )] = None
    ) -> Dict[str, Any]:
        """
        List channels matching the API request parameters.
        
        Must specify exactly one filter: for_handle, for_username, id, managed_by_me, or mine.
        The 'part' parameter is required and specifies which channel properties to retrieve.
        """
        try:
            # Parse boolean parameters that might come as strings
            managed_by_me_bool = parse_bool_param(managed_by_me)
            mine_bool = parse_bool_param(mine)
            
            # Validate that exactly one filter is provided
            filters_provided = sum([
                for_handle is not None,
                for_username is not None,
                id is not None,
                managed_by_me_bool is not None,
                mine_bool is not None
            ])
            
            if filters_provided != 1:
                return {
                    "error": "Must specify exactly one filter: for_handle, for_username, id, managed_by_me, or mine"
                }
            
            # Parse numeric parameter
            max_results_int = parse_int_param(max_results, default=5)
            
            # Build request parameters
            params = {
                "part": ",".join(part),
                "maxResults": max_results_int
            }
            
            # Add filter parameters
            if for_handle:
                params["forHandle"] = for_handle
            if for_username:
                params["forUsername"] = for_username
            if id:
                params["id"] = id
            if managed_by_me_bool is not None:
                params["managedByMe"] = managed_by_me_bool
            if mine_bool is not None:
                params["mine"] = mine_bool
                
            # Add optional parameters
            if hl:
                params["hl"] = hl
            if page_token:
                params["pageToken"] = page_token
            
            # Make the API call
            response = await youtube_client.channels_list(**params)
            
            return {
                "totalResults": response.get("pageInfo", {}).get("totalResults", len(response.get("items", []))),
                "resultsPerPage": response.get("pageInfo", {}).get("resultsPerPage", len(response.get("items", []))),
                "nextPageToken": response.get("nextPageToken"),
                "prevPageToken": response.get("prevPageToken"),
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
    async def channels_update(
        id: Annotated[str, Field(
            description="The channel ID to update"
        )],
        country: Annotated[Optional[str], Field(
            default=None,
            description="Channel country (ISO 3166-1 alpha-2 code)"
        )] = None,
        description: Annotated[Optional[str], Field(
            default=None,
            description="Channel description"
        )] = None,
        default_language: Annotated[Optional[str], Field(
            default=None,
            description="Default language for channel (ISO 639-1 code)"
        )] = None,
        keywords: Annotated[Optional[str], Field(
            default=None,
            description="Channel keywords (space-separated)"
        )] = None,
        tracking_analytics_account_id: Annotated[Optional[str], Field(
            default=None,
            description="Google Analytics tracking ID"
        )] = None,
        unsubscribed_trailer: Annotated[Optional[str], Field(
            default=None,
            description="Video ID for unsubscribed viewers trailer"
        )] = None,
        self_declared_made_for_kids: Annotated[bool, Field(
            default=False,
            description="Channel made for kids designation"
        )] = False
    ) -> Dict[str, Any]:
        """
        Update a channel's metadata.
        
        Requires OAuth authentication and channel ownership.
        Currently limited to brandingSettings and status updates.
        Note: If a property is not specified, its existing value will be deleted.
        """
        try:
            # Check if at least one field is being updated
            updates_provided = any([
                country is not None,
                description is not None,
                default_language is not None,
                keywords is not None,
                tracking_analytics_account_id is not None,
                unsubscribed_trailer is not None,
                self_declared_made_for_kids
            ])
            
            if not updates_provided:
                return {
                    "error": "At least one field must be specified for update"
                }
            
            # Build update body
            body = {"id": id}
            parts = []
            
            # Add brandingSettings updates
            if any([country, description, default_language, keywords, 
                   tracking_analytics_account_id, unsubscribed_trailer]):
                branding_settings = {"channel": {}}
                
                if country is not None:
                    branding_settings["channel"]["country"] = country
                if description is not None:
                    branding_settings["channel"]["description"] = description
                if default_language is not None:
                    branding_settings["channel"]["defaultLanguage"] = default_language
                if keywords is not None:
                    branding_settings["channel"]["keywords"] = keywords
                if tracking_analytics_account_id is not None:
                    branding_settings["channel"]["trackingAnalyticsAccountId"] = tracking_analytics_account_id
                if unsubscribed_trailer is not None:
                    branding_settings["channel"]["unsubscribedTrailer"] = unsubscribed_trailer
                    
                body["brandingSettings"] = branding_settings
                parts.append("brandingSettings")
            
            # Add status updates
            if self_declared_made_for_kids:
                body["status"] = {
                    "selfDeclaredMadeForKids": self_declared_made_for_kids
                }
                parts.append("status")
            
            # Make the update
            response = await youtube_client.channels_update(
                part=",".join(parts),
                body=body
            )
            
            return {
                "success": True,
                "channel": response,
                "message": "Channel updated successfully"
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
    async def channels_list_videos(
        channel_id: Annotated[str, Field(
            description="The YouTube channel ID"
        )],
        max_results: Annotated[Union[int, str], Field(
            default=50,
            description="Maximum number of results to return"
        )] = 50,
        page_token: Annotated[Optional[str], Field(
            default=None,
            description="Token for pagination"
        )] = None
    ) -> Dict[str, Any]:
        """
        List videos from a specific channel.
        
        This is a convenience method that retrieves videos from a channel's uploads playlist.
        """
        try:
            # First, get the channel to find the uploads playlist
            channel_params = {
                "part": "snippet,contentDetails",
                "id": channel_id
            }
            
            channel_response = await youtube_client.channels_list(**channel_params)
            
            if not channel_response.get("items"):
                return {
                    "error": f"Channel with ID '{channel_id}' not found"
                }
            
            channel = channel_response["items"][0]
            
            # Get the uploads playlist ID
            uploads_playlist_id = channel["contentDetails"]["relatedPlaylists"]["uploads"]
            
            # Parse numeric parameter
            max_results_int = parse_int_param(max_results, default=50)
            
            # Get videos from the uploads playlist
            videos = await youtube_client.get_playlist_items(
                playlist_id=uploads_playlist_id,
                max_results=max_results_int
            )
            
            return {
                "channelId": channel_id,
                "channelTitle": channel["snippet"]["title"],
                "videoCount": len(videos),
                "videos": videos
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