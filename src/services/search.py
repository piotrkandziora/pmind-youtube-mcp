"""Search-related MCP tools implementing YouTube Search API v3"""

from typing import Dict, Any, Optional, Literal, Annotated, Union
from datetime import datetime
from pydantic import Field
from fastmcp import FastMCP
from ..config import Config
from ..utils import YouTubeClient, YouTubeAPIError, parse_bool_param, parse_int_param


def register_tools(mcp: FastMCP, config: Config, youtube_client: YouTubeClient):
    """Register search-related tools with the MCP server"""
    
    @mcp.tool
    async def search_list(
        q: Annotated[Optional[str], Field(
            default=None,
            description="Query term to search for. Supports Boolean NOT (-) and OR (|) operators"
        )] = None,
        type: Annotated[Literal["video", "channel", "playlist", "video,channel,playlist"], Field(
            default="video",
            description="Type of resource to search for"
        )] = "video",
        order: Annotated[Literal["date", "rating", "relevance", "title", "videoCount", "viewCount"], Field(
            default="relevance",
            description="Order to sort results"
        )] = "relevance",
        channel_id: Annotated[Optional[str], Field(
            default=None,
            description="Filter results to only include resources created by this channel"
        )] = None,
        max_results: Annotated[Union[int, str], Field(
            default=25,
            description="Maximum number of results to return"
        )] = 25,
        region_code: Annotated[Optional[str], Field(
            default=None,
            description="ISO 3166-1 alpha-2 country code to filter results"
        )] = None,
        relevance_language: Annotated[Optional[str], Field(
            default=None,
            description="ISO 639-1 two-letter language code to boost results relevant to this language"
        )] = None,
        safe_search: Annotated[Literal["moderate", "none", "strict"], Field(
            default="moderate",
            description="Filter search results by safety level"
        )] = "moderate",
        published_after: Annotated[Optional[str], Field(
            default=None,
            description="RFC 3339 formatted date-time (e.g., 2023-01-01T00:00:00Z)"
        )] = None,
        published_before: Annotated[Optional[str], Field(
            default=None,
            description="RFC 3339 formatted date-time (e.g., 2023-12-31T23:59:59Z)"
        )] = None,
        location: Annotated[Optional[str], Field(
            default=None,
            description="Latitude,longitude coordinates (e.g., '37.7749,-122.4194')"
        )] = None,
        location_radius: Annotated[Optional[str], Field(
            default=None,
            description="Search radius from location (e.g., '10km', '5mi'). Required if location is specified"
        )] = None,
        event_type: Annotated[Optional[Literal["completed", "live", "upcoming"]], Field(
            default=None,
            description="Filter video broadcasts by event type"
        )] = None,
        video_caption: Annotated[Optional[Literal["any", "closedCaption", "none"]], Field(
            default=None,
            description="Filter videos by caption availability"
        )] = None,
        video_category_id: Annotated[Optional[str], Field(
            default=None,
            description="Filter videos by category ID"
        )] = None,
        video_definition: Annotated[Optional[Literal["any", "high", "standard"]], Field(
            default=None,
            description="Filter videos by definition"
        )] = None,
        video_dimension: Annotated[Optional[Literal["2d", "3d", "any"]], Field(
            default=None,
            description="Filter videos by dimension"
        )] = None,
        video_duration: Annotated[Optional[Literal["any", "long", "medium", "short"]], Field(
            default=None,
            description="Filter videos by duration. short (<4min), medium (4-20min), long (>20min)"
        )] = None,
        video_embeddable: Annotated[Optional[Literal["any", "true"]], Field(
            default=None,
            description="Filter videos by embeddable status"
        )] = None,
        video_license: Annotated[Optional[Literal["any", "creativeCommon", "youtube"]], Field(
            default=None,
            description="Filter videos by license type"
        )] = None,
        video_syndicated: Annotated[Optional[Literal["any", "true"]], Field(
            default=None,
            description="Filter videos by syndicated status"
        )] = None,
        video_type: Annotated[Optional[Literal["any", "episode", "movie"]], Field(
            default=None,
            description="Filter videos by type"
        )] = None,
        page_token: Annotated[Optional[str], Field(
            default=None,
            description="Token for a specific results page"
        )] = None
    ) -> Dict[str, Any]:
        """
        Search for YouTube content using the comprehensive Search API.
        
        This implements the full YouTube Data API v3 search.list method with all parameters.
        At least one of 'q', 'channel_id', 'location', or other filters must be specified.
        """
        try:
            # Parse integer parameters
            max_results_int = parse_int_param(max_results, default=25)
            
            # Build search parameters
            search_params = {
                "type": type,
                "order": order,
                "maxResults": max_results_int,
                "safeSearch": safe_search
            }
            
            # Add optional parameters if provided
            if q:
                search_params["q"] = q
            if channel_id:
                search_params["channelId"] = channel_id
            if region_code:
                search_params["regionCode"] = region_code
            if relevance_language:
                search_params["relevanceLanguage"] = relevance_language
            if published_after:
                search_params["publishedAfter"] = published_after
            if published_before:
                search_params["publishedBefore"] = published_before
            if page_token:
                search_params["pageToken"] = page_token
                
            # Location parameters (both required together)
            if location:
                if not location_radius:
                    return {
                        "error": "location_radius is required when location is specified"
                    }
                search_params["location"] = location
                search_params["locationRadius"] = location_radius
            
            # Event type (only for videos)
            if event_type and "video" in type:
                search_params["eventType"] = event_type
            
            # Video-specific filters (only apply when searching for videos)
            if "video" in type:
                if video_caption:
                    search_params["videoCaption"] = video_caption
                if video_category_id:
                    search_params["videoCategoryId"] = video_category_id
                if video_definition:
                    search_params["videoDefinition"] = video_definition
                if video_dimension:
                    search_params["videoDimension"] = video_dimension
                if video_duration:
                    search_params["videoDuration"] = video_duration
                if video_embeddable:
                    search_params["videoEmbeddable"] = video_embeddable
                if video_license:
                    search_params["videoLicense"] = video_license
                if video_syndicated:
                    search_params["videoSyndicated"] = video_syndicated
                if video_type:
                    search_params["videoType"] = video_type
            
            # Validate that at least one search criteria is provided
            search_criteria = ["q", "channelId", "location", "eventType", "videoCaption", 
                             "videoCategoryId", "videoDefinition", "videoDimension", 
                             "videoDuration", "videoEmbeddable", "videoLicense", 
                             "videoSyndicated", "videoType"]
            
            if not any(param in search_params for param in search_criteria):
                return {
                    "error": "At least one search criterion must be specified (q, channel_id, location, or video filters)"
                }
            
            # Perform the search
            results = await youtube_client.search(**search_params)
            
            return {
                "query": q or "No query specified",
                "type": type,
                "resultCount": len(results["items"]),
                "totalResults": results.get("totalResults", len(results["items"])),
                "nextPageToken": results.get("nextPageToken"),
                "prevPageToken": results.get("prevPageToken"),
                "results": results["items"]
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