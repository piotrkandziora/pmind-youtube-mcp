"""Video-related MCP tools implementing YouTube Videos API v3"""

from typing import List, Optional, Dict, Any, Literal, Annotated, Union
from pydantic import Field
from fastmcp import FastMCP, Context
from ..config import Config
from ..utils import YouTubeClient, YouTubeAPIError, parse_int_param
from ..utils.upload_manager import UploadManager


def register_tools(mcp: FastMCP, config: Config, youtube_client: YouTubeClient):
    """Register video-related tools with the MCP server"""
    
    @mcp.tool
    async def videos_list(
        part: Annotated[List[str], Field(
            description="Video resource properties to include (snippet, contentDetails, statistics, status, etc.)"
        )],
        chart: Annotated[Optional[Literal["mostPopular"]], Field(
            default=None,
            description="Retrieve most popular videos"
        )] = None,
        id: Annotated[Optional[str], Field(
            default=None,
            description="Comma-separated list of video IDs"
        )] = None,
        my_rating: Annotated[Optional[Literal["like", "dislike"]], Field(
            default=None,
            description="Return videos rated by authenticated user"
        )] = None,
        hl: Annotated[Optional[str], Field(
            default=None,
            description="Language for localized properties (ISO 639-1 two-letter code)"
        )] = None,
        max_results: Annotated[Union[int, str], Field(
            default=5,
            description="Maximum number of items to return (1-50)"
        )] = 5,
        region_code: Annotated[Optional[str], Field(
            default=None,
            description="ISO 3166-1 alpha-2 country code"
        )] = None,
        page_token: Annotated[Optional[str], Field(
            default=None,
            description="Token for specific results page"
        )] = None,
        max_height: Annotated[Optional[Union[int, str]], Field(
            default=None,
            description="Maximum height of embedded player"
        )] = None,
        max_width: Annotated[Optional[Union[int, str]], Field(
            default=None,
            description="Maximum width of embedded player"
        )] = None,
        video_category_id: Annotated[Optional[str], Field(
            default=None,
            description="Filter by video category (only with chart=mostPopular)"
        )] = None
    ) -> Dict[str, Any]:
        """
        List videos matching the API request parameters.
        
        Must specify either 'chart', 'id', or 'my_rating' parameter.
        The 'part' parameter is required and specifies which video properties to retrieve.
        """
        try:
            # Parse integer parameters
            max_results_int = parse_int_param(max_results, default=5)
            max_height_int = parse_int_param(max_height)
            max_width_int = parse_int_param(max_width)
            
            # Validate that at least one filter is provided
            if not any([chart, id, my_rating]):
                return {
                    "error": "Must specify either 'chart', 'id', or 'my_rating' parameter"
                }
            
            # Build request parameters
            params = {
                "part": ",".join(part),
                "maxResults": max_results_int
            }
            
            # Add filter parameters
            if chart:
                params["chart"] = chart
            if id:
                params["id"] = id
            if my_rating:
                params["myRating"] = my_rating
                
            # Add optional parameters
            if hl:
                params["hl"] = hl
            if region_code:
                params["regionCode"] = region_code
            if page_token:
                params["pageToken"] = page_token
            if max_height_int:
                params["maxHeight"] = max_height_int
            if max_width_int:
                params["maxWidth"] = max_width_int
            if video_category_id and chart == "mostPopular":
                params["videoCategoryId"] = video_category_id
            
            # Make the API call
            response = await youtube_client.videos_list(**params)
            
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
    async def videos_get_rating(
        id: Annotated[str, Field(
            description="Comma-separated list of video IDs to get ratings for"
        )]
    ) -> Dict[str, Any]:
        """
        Get the ratings that the authenticated user gave to specified videos.
        
        Requires OAuth authentication. Returns rating information for each video.
        """
        try:
            response = await youtube_client.videos_get_rating(id)
            
            return {
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
    async def videos_rate(
        id: Annotated[str, Field(
            description="The YouTube video ID"
        )],
        rating: Annotated[Literal["like", "dislike", "none"], Field(
            description="Rating to apply: 'like', 'dislike', or 'none' (removes rating)"
        )]
    ) -> Dict[str, Any]:
        """
        Add a like or dislike rating to a video or remove a rating.
        
        Requires OAuth authentication. This updates the authenticated user's rating for the video.
        """
        try:
            await youtube_client.videos_rate(id=id, rating=rating)
            
            return {
                "success": True,
                "videoId": id,
                "rating": rating,
                "message": f"Successfully {'removed rating from' if rating == 'none' else f'{rating}d'} video"
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
    async def videos_update(
        id: Annotated[str, Field(
            description="The video ID to update"
        )],
        title: Annotated[Optional[str], Field(
            default=None,
            description="New video title"
        )] = None,
        description: Annotated[Optional[str], Field(
            default=None,
            description="New video description"
        )] = None,
        tags: Annotated[Optional[List[str]], Field(
            default=None,
            description="New video tags"
        )] = None,
        category_id: Annotated[Optional[str], Field(
            default=None,
            description="New category ID"
        )] = None,
        privacy_status: Annotated[Optional[Literal["private", "public", "unlisted"]], Field(
            default=None,
            description="New privacy status"
        )] = None,
        embeddable: Annotated[bool, Field(
            default=False,
            description="Whether the video can be embedded"
        )] = False,
        license: Annotated[Optional[Literal["youtube", "creativeCommon"]], Field(
            default=None,
            description="Video license"
        )] = None,
        public_stats_viewable: Annotated[bool, Field(
            default=False,
            description="Whether video statistics are publicly viewable"
        )] = False,
        publish_at: Annotated[Optional[str], Field(
            default=None,
            description="Scheduled publish time (ISO 8601 format)"
        )] = None,
        self_declared_made_for_kids: Annotated[bool, Field(
            default=False,
            description="Whether video is made for kids"
        )] = False
    ) -> Dict[str, Any]:
        """
        Update a video's metadata.
        
        Requires OAuth authentication and ownership of the video.
        At least one field must be specified for update.
        """
        try:
            # Check if at least one field is being updated
            updates_provided = any([
                title is not None,
                description is not None,
                tags is not None,
                category_id is not None,
                privacy_status is not None,
                embeddable,
                license is not None,
                public_stats_viewable,
                publish_at is not None,
                self_declared_made_for_kids
            ])
            
            if not updates_provided:
                return {
                    "error": "At least one field must be specified for update"
                }
            
            # Build update body
            body = {"id": id}
            parts = []
            
            # Add snippet updates
            if any([title is not None, description is not None, tags is not None, category_id is not None]):
                snippet = {}
                if title is not None:
                    snippet["title"] = title
                if description is not None:
                    snippet["description"] = description
                if tags is not None:
                    snippet["tags"] = tags
                if category_id is not None:
                    snippet["categoryId"] = category_id
                body["snippet"] = snippet
                parts.append("snippet")
            
            # Add status updates
            if any([privacy_status is not None, embeddable is not None, license is not None,
                   public_stats_viewable, publish_at is not None,
                   self_declared_made_for_kids]):
                status = {}
                if privacy_status is not None:
                    status["privacyStatus"] = privacy_status
                if embeddable:
                    status["embeddable"] = embeddable
                if license is not None:
                    status["license"] = license
                if public_stats_viewable:
                    status["publicStatsViewable"] = public_stats_viewable
                if publish_at is not None:
                    status["publishAt"] = publish_at
                if self_declared_made_for_kids:
                    status["selfDeclaredMadeForKids"] = self_declared_made_for_kids
                body["status"] = status
                parts.append("status")
            
            # Make the update
            response = await youtube_client.videos_update(
                part=",".join(parts),
                body=body
            )
            
            return {
                "success": True,
                "video": response,
                "message": "Video updated successfully"
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
    async def videos_delete(
        id: Annotated[str, Field(
            description="The YouTube video ID to delete"
        )]
    ) -> Dict[str, Any]:
        """
        Delete a YouTube video.
        
        Requires OAuth authentication and ownership of the video.
        This action cannot be undone.
        """
        try:
            await youtube_client.videos_delete(id=id)
            
            return {
                "success": True,
                "videoId": id,
                "message": "Video deleted successfully"
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
    async def videos_report_abuse(
        video_id: Annotated[str, Field(
            description="The YouTube video ID to report"
        )],
        reason_id: Annotated[str, Field(
            description="Primary reason for reporting (use 'S' for sexual content, 'V' for violent content, etc.)"
        )],
        secondary_reason_id: Annotated[Optional[str], Field(
            default=None,
            description="More specific reason ID"
        )] = None,
        comments: Annotated[Optional[str], Field(
            default=None,
            description="Additional information about the abuse"
        )] = None,
        language: Annotated[Optional[str], Field(
            default=None,
            description="Language of the reporter (ISO 639-1 two-letter code)"
        )] = None
    ) -> Dict[str, Any]:
        """
        Report a video for abusive content.
        
        Requires OAuth authentication. Common reason IDs:
        - 'S': Sexual content
        - 'V': Violent or repulsive content
        - 'H': Hateful or abusive content
        - 'D': Harmful dangerous acts
        - 'C': Child abuse
        - 'P': Spam or misleading
        """
        try:
            body = {
                "videoId": video_id,
                "reasonId": reason_id
            }
            
            if secondary_reason_id:
                body["secondaryReasonId"] = secondary_reason_id
            if comments:
                body["comments"] = comments
            if language:
                body["language"] = language
            
            await youtube_client.videos_report_abuse(body=body)
            
            return {
                "success": True,
                "videoId": video_id,
                "message": "Video reported successfully"
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
    
    # Initialize upload manager
    upload_manager = UploadManager(state_dir=config.upload_state_dir)
    
    @mcp.tool
    async def videos_upload_initiate(
        file_path: Annotated[str, Field(
            description="Path to the video file to upload"
        )],
        title: Annotated[str, Field(
            description="Title for the video"
        )],
        description: Annotated[Optional[str], Field(
            default="",
            description="Description for the video"
        )] = "",
        tags: Annotated[Optional[List[str]], Field(
            default=None,
            description="List of tags for the video"
        )] = None,
        category_id: Annotated[Optional[str], Field(
            default=None,
            description="YouTube category ID (optional)"
        )] = None,
        privacy_status: Annotated[Optional[Literal["private", "unlisted", "public"]], Field(
            default="private",
            description="Privacy status for the video"
        )] = "private",
        ctx: Optional[Context] = None
    ) -> Dict[str, Any]:
        """
        Initiate a background video upload to YouTube.
        
        This starts an upload process in the background and returns immediately
        with a session ID. Use videos_upload_status to check progress.
        
        Note: Large video uploads can take significant time. The upload continues
        even if the MCP connection is closed.
        """
        try:
            # Report starting
            if ctx:
                await ctx.info(f"Initiating upload for: {title}")
            
            result = upload_manager.start_upload(
                file_path=file_path,
                title=title,
                description=description,
                tags=tags,
                category_id=category_id,
                privacy_status=privacy_status,
                client_secrets_file=config.client_secrets_file,
                token_file=config.token_file
            )
            
            return {
                "success": True,
                **result,
                "message": "Upload started in background. Use videos_upload_status to check progress."
            }
            
        except FileNotFoundError as e:
            return {
                "error": str(e)
            }
        except Exception as e:
            return {
                "error": f"Failed to start upload: {str(e)}"
            }
    
    @mcp.tool
    async def videos_upload_status(
        session_id: Annotated[str, Field(
            description="Upload session ID returned by videos_upload_initiate"
        )]
    ) -> Dict[str, Any]:
        """
        Check the status of a background video upload.
        
        Returns current progress, status, and other upload information.
        Status can be: starting, uploading, processing, completed, failed, cancelled
        """
        try:
            status = upload_manager.get_status(session_id)
            
            if "error" in status and "not found" in status["error"]:
                return {
                    "error": f"Upload session not found: {session_id}"
                }
            
            # Format response based on status
            result = {
                "session_id": status["session_id"],
                "status": status["status"],
                "progress": status.get("progress", 0),
                "file_path": status.get("file_path"),
                "title": status.get("title")
            }
            
            if status["status"] == "uploading":
                result["bytes_uploaded"] = status.get("bytes_uploaded", 0)
                result["total_bytes"] = status.get("total_bytes", 0)
                result["progress_percent"] = round(status.get("progress", 0) * 100, 1)
                if "upload_rate_mbps" in status:
                    result["upload_rate_mbps"] = round(status["upload_rate_mbps"], 2)
                if "eta_seconds" in status:
                    result["eta_seconds"] = status["eta_seconds"]
                    result["eta_formatted"] = f"{status['eta_seconds'] // 60}m {status['eta_seconds'] % 60}s"
            
            elif status["status"] == "completed":
                result["video_id"] = status.get("video_id")
                result["video_url"] = f"https://youtube.com/watch?v={status.get('video_id')}"
                result["completed_at"] = status.get("completed_at")
            
            elif status["status"] in ["failed", "cancelled"]:
                result["error"] = status.get("error", "Unknown error")
            
            result["started_at"] = status.get("started_at")
            result["updated_at"] = status.get("updated_at")
            
            return result
            
        except Exception as e:
            return {
                "error": f"Failed to get status: {str(e)}"
            }
    
    @mcp.tool
    async def videos_upload_list(
        active_only: Annotated[bool, Field(
            default=False,
            description="Only show active uploads (uploading/processing/starting)"
        )] = False
    ) -> Dict[str, Any]:
        """
        List all upload sessions.
        
        Returns a list of all upload sessions with their current status.
        Use active_only=true to see only uploads in progress.
        """
        try:
            uploads = upload_manager.list_uploads(active_only=active_only)
            
            # Format uploads for display
            formatted_uploads = []
            for upload in uploads:
                formatted = {
                    "session_id": upload["session_id"],
                    "status": upload["status"],
                    "title": upload.get("title", "Unknown"),
                    "progress": round(upload.get("progress", 0) * 100, 1),
                    "started_at": upload.get("started_at")
                }
                
                if upload["status"] == "completed":
                    formatted["video_id"] = upload.get("video_id")
                elif upload["status"] in ["failed", "cancelled"]:
                    formatted["error"] = upload.get("error")
                
                formatted_uploads.append(formatted)
            
            return {
                "uploads": formatted_uploads,
                "total": len(formatted_uploads),
                "active": len([u for u in formatted_uploads if u["status"] in ["uploading", "processing", "starting"]])
            }
            
        except Exception as e:
            return {
                "error": f"Failed to list uploads: {str(e)}"
            }
    
    @mcp.tool
    async def videos_upload_cancel(
        session_id: Annotated[str, Field(
            description="Upload session ID to cancel"
        )]
    ) -> Dict[str, Any]:
        """
        Cancel a background video upload.
        
        This will terminate the upload process if it's still running.
        Note: Partially uploaded videos are not saved on YouTube.
        """
        try:
            result = upload_manager.cancel_upload(session_id)
            
            if "error" in result:
                return result
            
            return {
                "success": True,
                **result
            }
            
        except Exception as e:
            return {
                "error": f"Failed to cancel upload: {str(e)}"
            }