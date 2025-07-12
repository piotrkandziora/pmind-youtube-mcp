"""YouTube API client wrapper with error handling"""

import asyncio
import json
import logging
import os
from typing import List, Dict, Any, Optional
from functools import wraps
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

logger = logging.getLogger(__name__)


class YouTubeAPIError(Exception):
    """Custom exception for YouTube API errors"""
    def __init__(self, message: str, status_code: Optional[int] = None, details: Optional[dict] = None):
        super().__init__(message)
        self.status_code = status_code
        self.details = details


def async_wrap(func):
    """Wrap synchronous functions to make them async"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        # run_in_executor doesn't support kwargs, so we need to use a lambda
        return await loop.run_in_executor(None, lambda: func(*args, **kwargs))
    return wrapper


class YouTubeClient:
    """Async wrapper for YouTube Data API v3"""
    
    # OAuth scopes required for full functionality
    SCOPES = [
        'https://www.googleapis.com/auth/youtube.force-ssl',
        'https://www.googleapis.com/auth/youtube'
    ]
    
    def __init__(self, client_secrets_file: str = "client_secrets.json", token_file: str = "token.json"):
        self._quota_used = 0
        self._token_file = token_file
        logger.debug("Initializing YouTube client with OAuth authentication")
        self._init_oauth(client_secrets_file)
    
    def _init_oauth(self, client_secrets_file: str):
        """Initialize OAuth authentication"""
        creds = None
        token_file = self._token_file
        
        # Load existing token if available
        if os.path.exists(token_file):
            try:
                creds = Credentials.from_authorized_user_file(token_file, self.SCOPES)
                logger.debug("Loaded existing OAuth token")
            except Exception as e:
                logger.warning(f"Failed to load existing token: {e}")
        
        # If there are no (valid) credentials available, let the user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                logger.debug("Refreshing expired OAuth token")
                creds.refresh(Request())
            else:
                if not os.path.exists(client_secrets_file):
                    raise FileNotFoundError(
                        f"Client secrets file '{client_secrets_file}' not found. "
                        "Download it from Google Cloud Console."
                    )
                
                logger.info("Starting OAuth flow - check your browser")
                flow = InstalledAppFlow.from_client_secrets_file(
                    client_secrets_file, self.SCOPES)
                creds = flow.run_local_server(port=0)
                
            # Save the credentials for the next run
            with open(token_file, 'w') as token:
                token.write(creds.to_json())
                logger.debug("Saved OAuth token for future use")
        
        # Build the YouTube service with OAuth credentials
        try:
            self.youtube = build('youtube', 'v3', credentials=creds)
            logger.debug("YouTube client initialized successfully with OAuth")
        except Exception as e:
            logger.error(f"Failed to initialize YouTube client with OAuth: {type(e).__name__}: {str(e)}")
            raise
    
    def _handle_error(self, error: HttpError) -> YouTubeAPIError:
        """Convert Google API errors to our custom exception"""
        try:
            status_code = error.resp.status if hasattr(error, 'resp') else None
            
            # Try to parse the error response JSON
            error_data = {}
            error_reason = None
            error_message = None
            
            try:
                import json
                if hasattr(error, 'content'):
                    error_data = json.loads(error.content.decode('utf-8'))
                    if 'error' in error_data:
                        errors = error_data['error'].get('errors', [])
                        if errors:
                            error_reason = errors[0].get('reason')
                            error_message = errors[0].get('message')
            except:
                # Fallback to string parsing
                error_reason = str(error)
            
            # Handle specific status codes and error reasons
            if status_code == 400:
                if error_reason == 'invalidParameter':
                    return YouTubeAPIError(
                        f"Invalid parameter value: {error_message or 'Check your request parameters'}",
                        status_code=400,
                        details=error_data
                    )
                elif error_reason == 'keyInvalid':
                    return YouTubeAPIError(
                        "Invalid API key. Please check your credentials.",
                        status_code=400,
                        details=error_data
                    )
                elif error_reason == 'required':
                    return YouTubeAPIError(
                        f"Required parameter missing: {error_message or 'Check API documentation'}",
                        status_code=400,
                        details=error_data
                    )
                else:
                    return YouTubeAPIError(
                        f"Bad request: {error_message or 'Invalid request parameters'}",
                        status_code=400,
                        details=error_data
                    )
            
            elif status_code == 401:
                if error_reason == 'authError':
                    return YouTubeAPIError(
                        "Authentication failed. Please check your OAuth token.",
                        status_code=401,
                        details=error_data
                    )
                else:
                    return YouTubeAPIError(
                        "Unauthorized. Please authenticate with valid credentials.",
                        status_code=401,
                        details=error_data
                    )
            
            elif status_code == 403:
                if error_reason == 'quotaExceeded':
                    return YouTubeAPIError(
                        "YouTube API quota exceeded. Please try again later or upgrade your quota.",
                        status_code=403,
                        details=error_data
                    )
                elif error_reason == 'insufficientPermissions':
                    return YouTubeAPIError(
                        "Insufficient permissions. Check OAuth scopes or channel permissions.",
                        status_code=403,
                        details=error_data
                    )
                elif error_reason == 'dailyLimitExceeded':
                    return YouTubeAPIError(
                        "Daily API limit exceeded. Please try again tomorrow.",
                        status_code=403,
                        details=error_data
                    )
                elif error_reason == 'channelSuspended':
                    return YouTubeAPIError(
                        "Channel is suspended and cannot perform this action.",
                        status_code=403,
                        details=error_data
                    )
                else:
                    return YouTubeAPIError(
                        f"Access forbidden: {error_message or 'Check permissions and API access'}",
                        status_code=403,
                        details=error_data
                    )
            
            elif status_code == 404:
                return YouTubeAPIError(
                    f"Resource not found: {error_message or 'The requested resource does not exist'}",
                    status_code=404,
                    details=error_data
                )
            
            elif status_code == 429:
                return YouTubeAPIError(
                    "Rate limit exceeded. Please implement exponential backoff and retry.",
                    status_code=429,
                    details=error_data
                )
            
            elif status_code in [500, 502, 503]:
                return YouTubeAPIError(
                    f"YouTube server error ({status_code}). Please retry the request.",
                    status_code=status_code,
                    details=error_data
                )
            
            else:
                return YouTubeAPIError(
                    f"YouTube API error: {error_message or str(error)}",
                    status_code=status_code,
                    details=error_data
                )
        except Exception as e:
            logger.error(f"Error parsing API error: {e}")
            return YouTubeAPIError(f"Unknown error: {str(error)}")
    
    @async_wrap
    def search(self, **kwargs) -> Dict[str, Any]:
        """Comprehensive search using YouTube Data API v3
        
        Supports all search.list parameters including type, order, filters, etc.
        Returns the full API response including pagination tokens.
        """
        try:
            # Build the search request with all provided parameters
            request = self.youtube.search().list(
                part='snippet',
                **kwargs
            )
            response = request.execute()
            
            # Log the raw response for debugging
            logger.debug(f"YouTube API search response: {json.dumps(response, indent=2)}")
            
            self._quota_used += 100  # Search costs 100 quota units
            
            # Add totalResults if available from pageInfo
            if 'pageInfo' in response and 'totalResults' in response['pageInfo']:
                response['totalResults'] = response['pageInfo']['totalResults']
            
            return response
            
        except HttpError as e:
            logger.error(f"HTTP Error in search: {str(e)}")
            raise self._handle_error(e)
        except Exception as e:
            logger.error(f"Unexpected error in search: {type(e).__name__}: {str(e)}")
            raise
    
    @async_wrap
    def videos_list(self, **kwargs) -> Dict[str, Any]:
        """List videos using YouTube Data API v3 videos.list method"""
        try:
            request = self.youtube.videos().list(**kwargs)
            response = request.execute()
            self._quota_used += 1  # Videos.list costs 1 quota unit
            return response
        except HttpError as e:
            raise self._handle_error(e)
    
    @async_wrap
    def videos_get_rating(self, id: str) -> Dict[str, Any]:
        """Get ratings for videos"""
        try:
            request = self.youtube.videos().getRating(id=id)
            response = request.execute()
            self._quota_used += 1
            return response
        except HttpError as e:
            raise self._handle_error(e)
    
    @async_wrap
    def videos_rate(self, id: str, rating: str) -> None:
        """Rate a video"""
        try:
            request = self.youtube.videos().rate(id=id, rating=rating)
            request.execute()
            self._quota_used += 50  # Rate costs 50 quota units
        except HttpError as e:
            raise self._handle_error(e)
    
    @async_wrap
    def videos_update(self, part: str, body: dict) -> Dict[str, Any]:
        """Update video metadata"""
        try:
            request = self.youtube.videos().update(part=part, body=body)
            response = request.execute()
            self._quota_used += 50  # Update costs 50 quota units
            return response
        except HttpError as e:
            raise self._handle_error(e)
    
    @async_wrap
    def videos_delete(self, id: str) -> None:
        """Delete a video"""
        try:
            request = self.youtube.videos().delete(id=id)
            request.execute()
            self._quota_used += 50  # Delete costs 50 quota units
        except HttpError as e:
            raise self._handle_error(e)
    
    @async_wrap
    def videos_report_abuse(self, body: dict) -> None:
        """Report a video for abuse"""
        try:
            request = self.youtube.videos().reportAbuse(body=body)
            request.execute()
            self._quota_used += 50  # ReportAbuse costs 50 quota units
        except HttpError as e:
            raise self._handle_error(e)
    
    @async_wrap
    def videos_insert(self, part: str, body: dict, media_body=None) -> Dict[str, Any]:
        """Insert (upload) a new video"""
        try:
            request = self.youtube.videos().insert(
                part=part,
                body=body,
                media_body=media_body
            )
            response = request.execute()
            self._quota_used += 1600  # Videos.insert costs 1600 quota units
            return response
        except HttpError as e:
            raise self._handle_error(e)
    
    @async_wrap
    def channels_list(self, **kwargs) -> Dict[str, Any]:
        """List channels using YouTube Data API v3 channels.list method"""
        try:
            request = self.youtube.channels().list(**kwargs)
            response = request.execute()
            self._quota_used += 1  # Channels.list costs 1 quota unit
            return response
        except HttpError as e:
            raise self._handle_error(e)
    
    @async_wrap
    def channels_update(self, part: str, body: dict) -> Dict[str, Any]:
        """Update channel metadata"""
        try:
            request = self.youtube.channels().update(part=part, body=body)
            response = request.execute()
            self._quota_used += 50  # Update costs 50 quota units
            return response
        except HttpError as e:
            raise self._handle_error(e)
    
    @async_wrap
    def captions_list(self, **kwargs) -> Dict[str, Any]:
        """List caption tracks for a video"""
        try:
            request = self.youtube.captions().list(**kwargs)
            response = request.execute()
            self._quota_used += 50  # Captions.list costs 50 quota units
            return response
        except HttpError as e:
            raise self._handle_error(e)
    
    @async_wrap
    def captions_download(self, **kwargs) -> str:
        """Download caption track content"""
        try:
            request = self.youtube.captions().download(**kwargs)
            response = request.execute()
            # Note: This returns the actual caption content as text
            return response
        except HttpError as e:
            raise self._handle_error(e)
    
    @async_wrap
    def captions_update(self, part: str, body: dict) -> Dict[str, Any]:
        """Update caption track"""
        try:
            request = self.youtube.captions().update(part=part, body=body)
            response = request.execute()
            self._quota_used += 50  # Update costs 50 quota units
            return response
        except HttpError as e:
            raise self._handle_error(e)
    
    @async_wrap
    def captions_delete(self, id: str) -> None:
        """Delete a caption track"""
        try:
            request = self.youtube.captions().delete(id=id)
            request.execute()
            self._quota_used += 50  # Delete costs 50 quota units
        except HttpError as e:
            raise self._handle_error(e)
    
    @async_wrap
    def channel_banners_insert(self, image_path: str) -> Dict[str, Any]:
        """Upload channel banner image"""
        try:
            # This would require MediaFileUpload from googleapiclient.http
            # For now, return a placeholder
            # In real implementation:
            # media = MediaFileUpload(image_path, mimetype='image/jpeg')
            # request = self.youtube.channelBanners().insert(media_body=media)
            # response = request.execute()
            raise NotImplementedError(
                "Channel banner upload requires file upload implementation. "
                "This would typically use googleapiclient.http.MediaFileUpload"
            )
        except HttpError as e:
            raise self._handle_error(e)
    
    @async_wrap
    def channel_sections_list(self, **kwargs) -> Dict[str, Any]:
        """List channel sections"""
        try:
            request = self.youtube.channelSections().list(**kwargs)
            response = request.execute()
            self._quota_used += 1  # List costs 1 quota unit
            return response
        except HttpError as e:
            raise self._handle_error(e)
    
    @async_wrap
    def channel_sections_insert(self, part: str, body: dict) -> Dict[str, Any]:
        """Insert a channel section"""
        try:
            request = self.youtube.channelSections().insert(part=part, body=body)
            response = request.execute()
            self._quota_used += 50  # Insert costs 50 quota units
            return response
        except HttpError as e:
            raise self._handle_error(e)
    
    @async_wrap
    def channel_sections_update(self, part: str, body: dict) -> Dict[str, Any]:
        """Update a channel section"""
        try:
            request = self.youtube.channelSections().update(part=part, body=body)
            response = request.execute()
            self._quota_used += 50  # Update costs 50 quota units
            return response
        except HttpError as e:
            raise self._handle_error(e)
    
    @async_wrap
    def channel_sections_delete(self, id: str) -> None:
        """Delete a channel section"""
        try:
            request = self.youtube.channelSections().delete(id=id)
            request.execute()
            self._quota_used += 50  # Delete costs 50 quota units
        except HttpError as e:
            raise self._handle_error(e)
    
    @async_wrap
    def comments_list(self, **kwargs) -> Dict[str, Any]:
        """List comments"""
        try:
            request = self.youtube.comments().list(**kwargs)
            response = request.execute()
            self._quota_used += 1  # Comments.list costs 1 quota unit
            return response
        except HttpError as e:
            raise self._handle_error(e)
    
    @async_wrap
    def comments_insert(self, part: str, body: dict) -> Dict[str, Any]:
        """Insert a comment reply"""
        try:
            request = self.youtube.comments().insert(part=part, body=body)
            response = request.execute()
            self._quota_used += 50  # Insert costs 50 quota units
            return response
        except HttpError as e:
            raise self._handle_error(e)
    
    @async_wrap
    def comments_update(self, part: str, body: dict) -> Dict[str, Any]:
        """Update a comment"""
        try:
            request = self.youtube.comments().update(part=part, body=body)
            response = request.execute()
            self._quota_used += 50  # Update costs 50 quota units
            return response
        except HttpError as e:
            raise self._handle_error(e)
    
    @async_wrap
    def comments_delete(self, id: str) -> None:
        """Delete a comment"""
        try:
            request = self.youtube.comments().delete(id=id)
            request.execute()
            self._quota_used += 50  # Delete costs 50 quota units
        except HttpError as e:
            raise self._handle_error(e)
    
    @async_wrap
    def comments_set_moderation_status(self, **kwargs) -> None:
        """Set comment moderation status"""
        try:
            request = self.youtube.comments().setModerationStatus(**kwargs)
            request.execute()
            self._quota_used += 50  # SetModerationStatus costs 50 quota units
        except HttpError as e:
            raise self._handle_error(e)
    
    @async_wrap
    def comment_threads_list(self, **kwargs) -> Dict[str, Any]:
        """List comment threads"""
        try:
            request = self.youtube.commentThreads().list(**kwargs)
            response = request.execute()
            self._quota_used += 1  # CommentThreads.list costs 1 quota unit
            return response
        except HttpError as e:
            raise self._handle_error(e)
    
    @async_wrap
    def comment_threads_insert(self, part: str, body: dict) -> Dict[str, Any]:
        """Insert a top-level comment"""
        try:
            request = self.youtube.commentThreads().insert(part=part, body=body)
            response = request.execute()
            self._quota_used += 50  # Insert costs 50 quota units
            return response
        except HttpError as e:
            raise self._handle_error(e)
    
    @async_wrap
    def members_list(self, **kwargs) -> Dict[str, Any]:
        """List channel members"""
        try:
            request = self.youtube.members().list(**kwargs)
            response = request.execute()
            self._quota_used += 1  # Members.list costs 1 quota unit
            return response
        except HttpError as e:
            raise self._handle_error(e)
    
    @async_wrap
    def memberships_levels_list(self, **kwargs) -> Dict[str, Any]:
        """List membership levels"""
        try:
            request = self.youtube.membershipsLevels().list(**kwargs)
            response = request.execute()
            self._quota_used += 1  # MembershipsLevels.list costs 1 quota unit
            return response
        except HttpError as e:
            raise self._handle_error(e)
    
    @async_wrap
    def playlist_items_list(self, **kwargs) -> Dict[str, Any]:
        """List playlist items using YouTube Data API v3 playlistItems.list method"""
        try:
            request = self.youtube.playlistItems().list(**kwargs)
            response = request.execute()
            self._quota_used += 1  # PlaylistItems.list costs 1 quota unit
            return response
        except HttpError as e:
            raise self._handle_error(e)
    
    @async_wrap
    def playlist_items_insert(self, part: str, body: dict) -> Dict[str, Any]:
        """Insert an item into a playlist"""
        try:
            request = self.youtube.playlistItems().insert(part=part, body=body)
            response = request.execute()
            self._quota_used += 50  # Insert costs 50 quota units
            return response
        except HttpError as e:
            raise self._handle_error(e)
    
    @async_wrap
    def playlist_items_update(self, part: str, body: dict) -> Dict[str, Any]:
        """Update a playlist item"""
        try:
            request = self.youtube.playlistItems().update(part=part, body=body)
            response = request.execute()
            self._quota_used += 50  # Update costs 50 quota units
            return response
        except HttpError as e:
            raise self._handle_error(e)
    
    @async_wrap
    def playlist_items_delete(self, id: str) -> None:
        """Delete a playlist item"""
        try:
            request = self.youtube.playlistItems().delete(id=id)
            request.execute()
            self._quota_used += 50  # Delete costs 50 quota units
        except HttpError as e:
            raise self._handle_error(e)
    
    @async_wrap
    def get_playlist_items(self, playlist_id: str, max_results: int = 50) -> List[Dict[str, Any]]:
        """Get videos from a playlist"""
        try:
            items = []
            next_page_token = None
            
            while len(items) < max_results:
                request = self.youtube.playlistItems().list(
                    part='snippet,contentDetails',
                    playlistId=playlist_id,
                    maxResults=min(50, max_results - len(items)),
                    pageToken=next_page_token
                )
                response = request.execute()
                self._quota_used += 1  # PlaylistItems.list costs 1 quota unit
                
                for item in response.get('items', []):
                    video_item = {
                        'videoId': item['snippet']['resourceId']['videoId'],
                        'title': item['snippet']['title'],
                        'description': item['snippet']['description'],
                        'position': item['snippet']['position'],
                        'publishedAt': item['snippet']['publishedAt'],
                        'channelId': item['snippet']['channelId'],
                        'channelTitle': item['snippet']['channelTitle'],
                        'thumbnails': item['snippet']['thumbnails']
                    }
                    items.append(video_item)
                
                next_page_token = response.get('nextPageToken')
                if not next_page_token:
                    break
            
            return items
        except HttpError as e:
            raise self._handle_error(e)
    
    @async_wrap
    def playlists_list(self, **kwargs) -> Dict[str, Any]:
        """List playlists using YouTube Data API v3 playlists.list method"""
        try:
            request = self.youtube.playlists().list(**kwargs)
            response = request.execute()
            self._quota_used += 1  # Playlists.list costs 1 quota unit
            return response
        except HttpError as e:
            raise self._handle_error(e)
    
    @async_wrap
    def playlists_insert(self, part: str, body: dict) -> Dict[str, Any]:
        """Create a playlist"""
        try:
            request = self.youtube.playlists().insert(part=part, body=body)
            response = request.execute()
            self._quota_used += 50  # Insert costs 50 quota units
            return response
        except HttpError as e:
            raise self._handle_error(e)
    
    @async_wrap
    def playlists_update(self, part: str, body: dict) -> Dict[str, Any]:
        """Update playlist metadata"""
        try:
            request = self.youtube.playlists().update(part=part, body=body)
            response = request.execute()
            self._quota_used += 50  # Update costs 50 quota units
            return response
        except HttpError as e:
            raise self._handle_error(e)
    
    @async_wrap
    def playlists_delete(self, id: str) -> None:
        """Delete a playlist"""
        try:
            request = self.youtube.playlists().delete(id=id)
            request.execute()
            self._quota_used += 50  # Delete costs 50 quota units
        except HttpError as e:
            raise self._handle_error(e)
    
    @async_wrap
    def thumbnails_set(self, video_id: str, image_path: str) -> Dict[str, Any]:
        """Set video thumbnail"""
        try:
            # This would require MediaFileUpload from googleapiclient.http
            # For now, return a placeholder
            raise NotImplementedError(
                "Thumbnail upload requires file upload implementation. "
                "This would typically use googleapiclient.http.MediaFileUpload"
            )
        except HttpError as e:
            raise self._handle_error(e)
    
    @async_wrap
    def video_categories_list(self, **kwargs) -> Dict[str, Any]:
        """List video categories"""
        try:
            request = self.youtube.videoCategories().list(**kwargs)
            response = request.execute()
            self._quota_used += 1  # VideoCategories.list costs 1 quota unit
            return response
        except HttpError as e:
            raise self._handle_error(e)
    
    @async_wrap
    def watermarks_set(self, channel_id: str, image_path: str, **kwargs) -> Dict[str, Any]:
        """Set channel watermark"""
        try:
            # This would require MediaFileUpload from googleapiclient.http
            # For now, return a placeholder
            raise NotImplementedError(
                "Watermark upload requires file upload implementation. "
                "This would typically use googleapiclient.http.MediaFileUpload"
            )
        except HttpError as e:
            raise self._handle_error(e)
    
    @async_wrap
    def watermarks_unset(self, channel_id: str) -> None:
        """Remove channel watermark"""
        try:
            request = self.youtube.watermarks().unset(channelId=channel_id)
            request.execute()
            self._quota_used += 50  # Watermarks.unset costs 50 quota units
        except HttpError as e:
            raise self._handle_error(e)
    
    @async_wrap
    def i18n_regions_list(self, **kwargs) -> Dict[str, Any]:
        """List supported YouTube content regions"""
        try:
            request = self.youtube.i18nRegions().list(**kwargs)
            response = request.execute()
            self._quota_used += 1  # i18nRegions.list costs 1 quota unit
            return response
        except HttpError as e:
            raise self._handle_error(e)
    
    @async_wrap
    def i18n_languages_list(self, **kwargs) -> Dict[str, Any]:
        """List supported YouTube UI languages"""
        try:
            request = self.youtube.i18nLanguages().list(**kwargs)
            response = request.execute()
            self._quota_used += 1  # i18nLanguages.list costs 1 quota unit
            return response
        except HttpError as e:
            raise self._handle_error(e)
    
    @async_wrap
    def playlist_images_list(self, **kwargs) -> Dict[str, Any]:
        """List playlist thumbnail images"""
        try:
            request = self.youtube.playlistImages().list(**kwargs)
            response = request.execute()
            self._quota_used += 1  # PlaylistImages.list costs 1 quota unit
            return response
        except HttpError as e:
            raise self._handle_error(e)
    
    @async_wrap
    def playlist_images_insert(self, playlist_id: str, image_path: str) -> Dict[str, Any]:
        """Upload playlist thumbnail image"""
        try:
            # This would require MediaFileUpload from googleapiclient.http
            raise NotImplementedError(
                "Playlist image upload requires file upload implementation. "
                "This would typically use googleapiclient.http.MediaFileUpload"
            )
        except HttpError as e:
            raise self._handle_error(e)
    
    @async_wrap
    def playlist_images_update(self, id: str, playlist_id: str, image_path: str) -> Dict[str, Any]:
        """Update playlist thumbnail image"""
        try:
            # This would require MediaFileUpload from googleapiclient.http
            raise NotImplementedError(
                "Playlist image update requires file upload implementation. "
                "This would typically use googleapiclient.http.MediaFileUpload"
            )
        except HttpError as e:
            raise self._handle_error(e)
    
    @async_wrap
    def playlist_images_delete(self, id: str) -> None:
        """Delete playlist thumbnail image"""
        try:
            request = self.youtube.playlistImages().delete(id=id)
            request.execute()
            self._quota_used += 50  # PlaylistImages.delete costs 50 quota units
        except HttpError as e:
            raise self._handle_error(e)
    
    @async_wrap
    def get_playlist(self, playlist_id: str) -> Optional[Dict[str, Any]]:
        """Get playlist information"""
        try:
            request = self.youtube.playlists().list(
                part='snippet,contentDetails',
                id=playlist_id
            )
            response = request.execute()
            self._quota_used += 1  # Playlists.list costs 1 quota unit
            
            if response['items']:
                playlist = response['items'][0]
                return {
                    'id': playlist['id'],
                    'title': playlist['snippet']['title'],
                    'description': playlist['snippet']['description'],
                    'channelId': playlist['snippet']['channelId'],
                    'channelTitle': playlist['snippet']['channelTitle'],
                    'publishedAt': playlist['snippet']['publishedAt'],
                    'itemCount': playlist['contentDetails']['itemCount'],
                    'thumbnails': playlist['snippet']['thumbnails']
                }
            return None
        except HttpError as e:
            raise self._handle_error(e)
    
    @async_wrap
    def list_subscriptions(self, channel_id: Optional[str] = None, mine: bool = False, 
                          max_results: int = 50, for_channel_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List subscriptions for a channel or authenticated user"""
        try:
            params = {
                'part': 'snippet,contentDetails',
                'maxResults': max_results
            }
            
            # Must specify either channelId or mine
            if channel_id:
                params['channelId'] = channel_id
            elif mine:
                params['mine'] = True
            else:
                raise ValueError("Must specify either channel_id or mine=True")
            
            if for_channel_id:
                params['forChannelId'] = for_channel_id
            
            subscriptions = []
            next_page_token = None
            
            while len(subscriptions) < max_results:
                if next_page_token:
                    params['pageToken'] = next_page_token
                
                request = self.youtube.subscriptions().list(**params)
                response = request.execute()
                self._quota_used += 1  # Subscriptions.list costs 1 quota unit
                
                for item in response.get('items', []):
                    subscription = {
                        'subscriptionId': item['id'],
                        'channelId': item['snippet']['resourceId']['channelId'],
                        'channelTitle': item['snippet']['title'],
                        'description': item['snippet'].get('description', ''),
                        'publishedAt': item['snippet']['publishedAt'],
                        'thumbnails': item['snippet']['thumbnails']
                    }
                    
                    # Add content details if available
                    if 'contentDetails' in item:
                        subscription['totalItemCount'] = item['contentDetails'].get('totalItemCount', 0)
                        subscription['newItemCount'] = item['contentDetails'].get('newItemCount', 0)
                        subscription['activityType'] = item['contentDetails'].get('activityType', 'all')
                    
                    subscriptions.append(subscription)
                
                next_page_token = response.get('nextPageToken')
                if not next_page_token:
                    break
            
            return subscriptions
        except HttpError as e:
            raise self._handle_error(e)
    
    @async_wrap
    def list_recent_subscribers(self, max_results: int = 50) -> List[Dict[str, Any]]:
        """List recent subscribers to authenticated user's channel"""
        try:
            params = {
                'part': 'snippet,contentDetails',
                'myRecentSubscribers': True,
                'maxResults': max_results
            }
            
            subscribers = []
            next_page_token = None
            
            while len(subscribers) < max_results:
                if next_page_token:
                    params['pageToken'] = next_page_token
                
                request = self.youtube.subscriptions().list(**params)
                response = request.execute()
                self._quota_used += 1  # Subscriptions.list costs 1 quota unit
                
                for item in response.get('items', []):
                    subscriber = {
                        'subscriberId': item['snippet']['channelId'],
                        'subscriberTitle': item['snippet']['title'],
                        'description': item['snippet'].get('description', ''),
                        'subscribedAt': item['snippet']['publishedAt'],
                        'thumbnails': item['snippet']['thumbnails']
                    }
                    subscribers.append(subscriber)
                
                next_page_token = response.get('nextPageToken')
                if not next_page_token:
                    break
            
            return subscribers
        except HttpError as e:
            raise self._handle_error(e)
    
    @async_wrap
    def insert_subscription(self, channel_id: str) -> Dict[str, Any]:
        """Subscribe to a channel (requires OAuth authentication)"""
        try:
            # Build the request body
            body = {
                'snippet': {
                    'resourceId': {
                        'kind': 'youtube#channel',
                        'channelId': channel_id
                    }
                }
            }
            
            request = self.youtube.subscriptions().insert(
                part='snippet',
                body=body
            )
            response = request.execute()
            self._quota_used += 50  # Subscriptions.insert costs 50 quota units
            
            # Format the response
            return {
                'subscriptionId': response['id'],
                'channelId': response['snippet']['resourceId']['channelId'],
                'channelTitle': response['snippet'].get('title', ''),
                'description': response['snippet'].get('description', ''),
                'publishedAt': response['snippet']['publishedAt'],
                'thumbnails': response['snippet'].get('thumbnails', {}),
                'success': True
            }
        except HttpError as e:
            # Check if already subscribed
            if e.resp.status == 400 and 'subscriptionDuplicate' in str(e):
                raise YouTubeAPIError(
                    f"Already subscribed to channel {channel_id}",
                    status_code=400,
                    details={'reason': 'subscriptionDuplicate'}
                )
            raise self._handle_error(e)
    
    @async_wrap
    def delete_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """Delete a subscription (requires OAuth authentication)"""
        try:
            request = self.youtube.subscriptions().delete(
                id=subscription_id
            )
            request.execute()
            self._quota_used += 50  # Subscriptions.delete costs 50 quota units
            
            return {
                'subscriptionId': subscription_id,
                'deleted': True,
                'success': True
            }
        except HttpError as e:
            # Check for specific errors
            if e.resp.status == 404:
                raise YouTubeAPIError(
                    f"Subscription {subscription_id} not found",
                    status_code=404,
                    details={'reason': 'subscriptionNotFound'}
                )
            raise self._handle_error(e)
    
    def get_quota_used(self) -> int:
        """Get the approximate quota used in this session"""
        return self._quota_used