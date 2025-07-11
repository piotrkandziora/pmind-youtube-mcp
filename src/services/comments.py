"""Comment-related MCP tools implementing YouTube Comments API v3"""

from typing import List, Optional, Dict, Any, Literal, Annotated, Union
from pydantic import Field
from fastmcp import FastMCP
from ..config import Config
from ..utils import YouTubeClient, YouTubeAPIError, parse_bool_param, parse_int_param


def register_tools(mcp: FastMCP, config: Config, youtube_client: YouTubeClient):
    """Register comment-related tools with the MCP server"""
    
    @mcp.tool
    async def comments_list(
        part: Annotated[List[str], Field(
            description="Comment resource properties to include (snippet, id)"
        )],
        parent_id: Annotated[Optional[str], Field(
            default=None,
            description="Parent comment ID to get replies for"
        )] = None,
        id: Annotated[Optional[str], Field(
            default=None,
            description="Comma-separated list of comment IDs"
        )] = None,
        max_results: Annotated[Union[int, str], Field(
            default=20,
            description="Maximum number of items to return"
        )] = 20,
        page_token: Annotated[Optional[str], Field(
            default=None,
            description="Token for specific results page"
        )] = None,
        text_format: Annotated[Literal["html", "plainText"], Field(
            default="html",
            description="Format of the comment text"
        )] = "html"
    ) -> Dict[str, Any]:
        """
        List comments matching the request criteria.
        
        Must specify either parent_id (for replies) or id parameter.
        For top-level comments, use comment_threads_list instead.
        """
        try:
            # Parse integer parameters
            max_results_int = parse_int_param(max_results, default=20)
            
            # Validate that at least one filter is provided
            if not any([parent_id, id]):
                return {
                    "error": "Must specify either parent_id or id parameter"
                }
            
            # Build request parameters
            params = {
                "part": ",".join(part),
                "maxResults": max_results_int,
                "textFormat": text_format
            }
            
            # Add filter parameters
            if parent_id:
                params["parentId"] = parent_id
            if id:
                params["id"] = id
                
            # Add optional parameters
            if page_token:
                params["pageToken"] = page_token
            
            # Make the API call
            response = await youtube_client.comments_list(**params)
            
            return {
                "items": response.get("items", []),
                "nextPageToken": response.get("nextPageToken"),
                "pageInfo": response.get("pageInfo", {})
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
    async def comments_insert(
        parent_id: Annotated[str, Field(
            description="ID of the comment to reply to"
        )],
        text: Annotated[str, Field(
            description="The comment text"
        )]
    ) -> Dict[str, Any]:
        """
        Create a reply to an existing comment.
        
        To create a top-level comment, use comment_threads_insert instead.
        Requires OAuth authentication.
        """
        try:
            # Build the request body
            body = {
                "snippet": {
                    "parentId": parent_id,
                    "textOriginal": text
                }
            }
            
            response = await youtube_client.comments_insert(
                part="snippet",
                body=body
            )
            
            return {
                "success": True,
                "comment": response,
                "message": "Reply posted successfully"
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
    async def comments_update(
        id: Annotated[str, Field(
            description="Comment ID to update"
        )],
        text: Annotated[str, Field(
            description="New comment text"
        )]
    ) -> Dict[str, Any]:
        """
        Update a comment's text.
        
        Requires OAuth authentication and comment ownership.
        """
        try:
            # Build update body
            body = {
                "id": id,
                "snippet": {
                    "textOriginal": text
                }
            }
            
            response = await youtube_client.comments_update(
                part="snippet",
                body=body
            )
            
            return {
                "success": True,
                "comment": response,
                "message": "Comment updated successfully"
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
    async def comments_delete(
        id: Annotated[str, Field(
            description="Comment ID to delete"
        )]
    ) -> Dict[str, Any]:
        """
        Delete a comment.
        
        Requires OAuth authentication and appropriate permissions.
        This action cannot be undone.
        """
        try:
            await youtube_client.comments_delete(id=id)
            
            return {
                "success": True,
                "commentId": id,
                "message": "Comment deleted successfully"
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
    async def comments_set_moderation_status(
        id: Annotated[str, Field(
            description="Comma-separated list of comment IDs"
        )],
        moderation_status: Annotated[Literal["heldForReview", "published", "rejected"], Field(
            description="New moderation status"
        )],
        ban_author: Annotated[bool, Field(
            default=False,
            description="Whether to ban the comment author (only for 'rejected' status)"
        )] = False
    ) -> Dict[str, Any]:
        """
        Set the moderation status of one or more comments.
        
        Must be authorized by the owner of the channel or video.
        Requires OAuth authentication.
        """
        try:
            params = {
                "id": id,
                "moderationStatus": moderation_status
            }
            
            # Add ban author parameter if rejecting
            if moderation_status == "rejected" and ban_author:
                params["banAuthor"] = True
            
            await youtube_client.comments_set_moderation_status(**params)
            
            return {
                "success": True,
                "commentIds": id.split(","),
                "moderationStatus": moderation_status,
                "bannedAuthor": ban_author if moderation_status == "rejected" else False,
                "message": f"Moderation status set to '{moderation_status}'"
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