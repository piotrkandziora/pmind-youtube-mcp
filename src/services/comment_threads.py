"""CommentThread-related MCP tools implementing YouTube CommentThreads API v3"""

from typing import List, Optional, Dict, Any, Literal, Annotated, Union
from pydantic import Field
from fastmcp import FastMCP
from ..config import Config
from ..utils import YouTubeClient, YouTubeAPIError, parse_bool_param, parse_int_param


def register_tools(mcp: FastMCP, config: Config, youtube_client: YouTubeClient):
    """Register comment thread-related tools with the MCP server"""
    
    @mcp.tool
    async def comment_threads_list(
        part: Annotated[List[str], Field(
            description="CommentThread resource properties to include (snippet, replies, id)"
        )],
        all_threads_related_to_channel_id: Annotated[Optional[str], Field(
            default=None,
            description="Return all threads associated with channel (videos and channel itself)"
        )] = None,
        channel_id: Annotated[Optional[str], Field(
            default=None,
            description="Return comment threads for channel's discussion tab"
        )] = None,
        id: Annotated[Optional[str], Field(
            default=None,
            description="Comma-separated list of comment thread IDs"
        )] = None,
        video_id: Annotated[Optional[str], Field(
            default=None,
            description="Return comment threads for this video"
        )] = None,
        max_results: Annotated[Union[int, str], Field(
            default=20,
            description="Maximum number of items to return"
        )] = 20,
        moderation_status: Annotated[Optional[Literal["heldForReview", "likelySpam", "published"]], Field(
            default=None,
            description="Filter by moderation status (requires channel owner auth)"
        )] = None,
        order: Annotated[Literal["time", "relevance"], Field(
            default="time",
            description="Order of comment threads"
        )] = "time",
        page_token: Annotated[Optional[str], Field(
            default=None,
            description="Token for specific results page"
        )] = None,
        search_terms: Annotated[Optional[str], Field(
            default=None,
            description="Search comment threads for terms"
        )] = None,
        text_format: Annotated[Literal["html", "plainText"], Field(
            default="html",
            description="Format of the comment text"
        )] = "html"
    ) -> Dict[str, Any]:
        """
        List comment threads matching the request criteria.
        
        Must specify exactly one filter: all_threads_related_to_channel_id, 
        channel_id, id, or video_id.
        """
        try:
            # Parse integer parameters
            max_results_int = parse_int_param(max_results, default=20)
            
            # Validate that exactly one filter is provided
            filters_provided = sum([
                all_threads_related_to_channel_id is not None,
                channel_id is not None,
                id is not None,
                video_id is not None
            ])
            
            if filters_provided != 1:
                return {
                    "error": "Must specify exactly one filter: all_threads_related_to_channel_id, channel_id, id, or video_id"
                }
            
            # Build request parameters
            params = {
                "part": ",".join(part),
                "maxResults": max_results_int,
                "order": order,
                "textFormat": text_format
            }
            
            # Add filter parameters
            if all_threads_related_to_channel_id:
                params["allThreadsRelatedToChannelId"] = all_threads_related_to_channel_id
            if channel_id:
                params["channelId"] = channel_id
            if id:
                params["id"] = id
            if video_id:
                params["videoId"] = video_id
                
            # Add optional parameters
            if moderation_status:
                params["moderationStatus"] = moderation_status
            if page_token:
                params["pageToken"] = page_token
            if search_terms:
                params["searchTerms"] = search_terms
            
            # Make the API call
            response = await youtube_client.comment_threads_list(**params)
            
            return {
                "items": response.get("items", []),
                "nextPageToken": response.get("nextPageToken"),
                "pageInfo": response.get("pageInfo", {}),
                "totalResults": response.get("pageInfo", {}).get("totalResults", len(response.get("items", [])))
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
    async def comment_threads_insert(
        text: Annotated[str, Field(
            description="The comment text"
        )],
        channel_id: Annotated[Optional[str], Field(
            default=None,
            description="Channel ID for channel comment"
        )] = None,
        video_id: Annotated[Optional[str], Field(
            default=None,
            description="Video ID for video comment"
        )] = None
    ) -> Dict[str, Any]:
        """
        Create a new top-level comment.
        
        Must specify either channel_id (for channel discussion) or video_id (for video comment).
        To reply to an existing comment, use comments_insert instead.
        Requires OAuth authentication.
        """
        try:
            # Validate that exactly one target is provided
            if not channel_id and not video_id:
                return {
                    "error": "Must specify either channel_id or video_id"
                }
            if channel_id and video_id:
                return {
                    "error": "Cannot specify both channel_id and video_id"
                }
            
            # Build the request body
            body = {
                "snippet": {
                    "topLevelComment": {
                        "snippet": {
                            "textOriginal": text
                        }
                    }
                }
            }
            
            if channel_id:
                body["snippet"]["channelId"] = channel_id
            if video_id:
                body["snippet"]["videoId"] = video_id
            
            response = await youtube_client.comment_threads_insert(
                part="snippet",
                body=body
            )
            
            return {
                "success": True,
                "commentThread": response,
                "message": "Comment posted successfully"
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