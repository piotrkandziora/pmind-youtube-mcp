"""Video screenshot extraction tools for capturing frames at specific timestamps"""

import re
import base64
from pathlib import Path
from typing import Dict, Any, Optional, List, Union, Annotated, Literal
from pydantic import Field
import cv2
import yt_dlp
from fastmcp import FastMCP
from ..config import Config
from ..utils import YouTubeClient


def parse_timestamp(timestamp: Union[str, int, float]) -> float:
    """
    Parse timestamp in various formats to seconds.
    
    Supported formats:
    - Integer/float: direct seconds (e.g., 90, 90.5)
    - String seconds: "90", "90.5"
    - HH:MM:SS format: "1:30:45"
    - MM:SS format: "2:30"
    - With decimal seconds: "1:30:45.5"
    """
    if isinstance(timestamp, (int, float)):
        return float(timestamp)
    
    if isinstance(timestamp, str):
        # Try to parse as simple number first
        try:
            return float(timestamp)
        except ValueError:
            pass
        
        # Parse time format HH:MM:SS or MM:SS
        time_pattern = r'^(?:(\d+):)?(\d+):(\d+(?:\.\d+)?)$'
        match = re.match(time_pattern, timestamp)
        
        if match:
            hours = int(match.group(1) or 0)
            minutes = int(match.group(2))
            seconds = float(match.group(3))
            return hours * 3600 + minutes * 60 + seconds
        
        raise ValueError(f"Invalid timestamp format: {timestamp}")


def register_tools(mcp: FastMCP, config: Config, youtube_client: YouTubeClient):
    """Register video screenshot tools with the MCP server"""
    
    @mcp.tool
    async def video_screenshot_at_timestamp(
        video_id: Annotated[str, Field(
            description="YouTube video ID or full URL"
        )],
        timestamp: Annotated[Union[str, int, float], Field(
            description="Timestamp to capture (seconds, 'MM:SS', or 'HH:MM:SS')"
        )],
        output_format: Annotated[Literal["file", "base64"], Field(
            default="file",
            description="Return format: 'file' saves to disk, 'base64' returns encoded image"
        )] = "file",
        quality: Annotated[Optional[str], Field(
            default=None,
            description="Video quality to use (144p, 240p, 360p, 480p, 720p, 1080p, best). Default: config value or 1080p"
        )] = None,
        output_path: Annotated[Optional[str], Field(
            default=None,
            description="Custom output path for file format (default: CONFIG_DIR/screenshots)"
        )] = None,
        image_format: Annotated[Literal["jpg", "png"], Field(
            default="jpg",
            description="Image format for the screenshot"
        )] = "jpg"
    ) -> Dict[str, Any]:
        """
        Capture a screenshot from a YouTube video at a specific timestamp.
        
        This tool downloads the video stream and extracts a frame at the specified time.
        Does not require YouTube API authentication.
        
        Examples:
        - timestamp="30" or timestamp=30 - capture at 30 seconds
        - timestamp="1:30" - capture at 1 minute 30 seconds  
        - timestamp="1:15:30" - capture at 1 hour 15 minutes 30 seconds
        - timestamp="90.5" - capture at 90.5 seconds
        
        Returns:
        - For 'file' format: path to saved image
        - For 'base64' format: base64 encoded image data
        """
        try:
            # Extract video ID from URL if needed
            if "youtube.com" in video_id or "youtu.be" in video_id:
                # Extract ID from URL using regex
                patterns = [
                    r'youtube\.com/watch\?v=([^&]+)',
                    r'youtu\.be/([^?]+)',
                    r'youtube\.com/embed/([^?]+)'
                ]
                for pattern in patterns:
                    match = re.search(pattern, video_id)
                    if match:
                        video_id = match.group(1)
                        break
            
            # Parse timestamp to seconds
            try:
                target_seconds = parse_timestamp(timestamp)
            except ValueError as e:
                return {
                    "error": "Invalid timestamp format",
                    "details": str(e),
                    "supported_formats": [
                        "Seconds: 30, 90.5",
                        "String seconds: '30', '90.5'", 
                        "MM:SS format: '1:30'",
                        "HH:MM:SS format: '1:15:30'"
                    ]
                }
            
            # Configure yt-dlp options
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'no_color': True,
            }
            
            # Get video info without downloading
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                video_url = f"https://www.youtube.com/watch?v={video_id}"
                try:
                    info_dict = ydl.extract_info(video_url, download=False)
                except Exception as e:
                    return {
                        "error": "Failed to fetch video information",
                        "details": str(e),
                        "video_id": video_id
                    }
                
                # Check if timestamp is within video duration
                duration = info_dict.get('duration', 0)
                if target_seconds > duration:
                    return {
                        "error": "Timestamp exceeds video duration",
                        "details": f"Requested {target_seconds}s but video is only {duration}s long",
                        "video_duration": duration,
                        "requested_timestamp": target_seconds
                    }
                
                # Get available formats
                formats = info_dict.get('formats', [])
                
                # Filter and select format based on quality preference
                video_formats = [f for f in formats if f.get('vcodec') != 'none']
                
                # Use config default if quality not specified
                if not quality:
                    if config.screenshot_default_quality:
                        quality = config.screenshot_default_quality
                    else:
                        # Default to 1080p if no config set
                        quality = "1080p"
                
                selected_format = None
                if quality:
                    # Map quality to height
                    quality_map = {
                        '144p': 144, '240p': 240, '360p': 360,
                        '480p': 480, '720p': 720, '1080p': 1080
                    }
                    
                    if quality == 'best':
                        # Select highest quality
                        selected_format = max(video_formats, 
                                             key=lambda x: x.get('height', 0))
                    elif quality in quality_map:
                        target_height = quality_map[quality]
                        # Find closest quality
                        for fmt in video_formats:
                            if fmt.get('height') == target_height:
                                selected_format = fmt
                                break
                        
                        # If exact match not found, get closest lower quality
                        if not selected_format:
                            lower_formats = [f for f in video_formats 
                                           if f.get('height', 0) <= target_height]
                            if lower_formats:
                                selected_format = max(lower_formats,
                                                    key=lambda x: x.get('height', 0))
                
                # Default to lowest quality for speed if not specified
                if not selected_format:
                    selected_format = min(video_formats,
                                        key=lambda x: x.get('height', 0))
                
                stream_url = selected_format.get('url')
                if not stream_url:
                    return {
                        "error": "No suitable video stream found",
                        "details": "Could not find a valid video URL"
                    }
                
                # Open video capture
                cap = cv2.VideoCapture(stream_url)
                try:
                    if not cap.isOpened():
                        return {
                            "error": "Failed to open video stream",
                            "details": "Could not access the video URL"
                        }
                    
                    # Get FPS and calculate frame number
                    fps = cap.get(cv2.CAP_PROP_FPS)
                    if fps <= 0:
                        fps = 30  # Default fallback
                    
                    target_frame = int(fps * target_seconds)
                    
                    # Seek to target frame
                    cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
                    
                    # Read the frame
                    ret, frame = cap.read()
                    
                    if not ret or frame is None:
                        return {
                            "error": "Failed to capture frame",
                            "details": f"Could not read frame at {target_seconds}s"
                        }
                finally:
                    cap.release()
                
                # Prepare output
                if output_format == "file":
                    # Determine output directory
                    if output_path:
                        output_dir = Path(output_path).parent
                        output_file = Path(output_path)
                    else:
                        output_dir = Path(config.config_dir) / "screenshots"
                        output_dir.mkdir(parents=True, exist_ok=True)
                        
                        # Generate filename
                        safe_title = re.sub(r'[^\w\s-]', '', info_dict.get('title', video_id))
                        safe_title = re.sub(r'[-\s]+', '-', safe_title)[:50]
                        timestamp_str = str(target_seconds).replace('.', '_')
                        filename = f"{safe_title}_{timestamp_str}s.{image_format}"
                        output_file = output_dir / filename
                    
                    # Save image
                    if image_format == "jpg":
                        cv2.imwrite(str(output_file), frame, 
                                  [cv2.IMWRITE_JPEG_QUALITY, 95])
                    else:  # png
                        cv2.imwrite(str(output_file), frame)
                    
                    return {
                        "success": True,
                        "video_id": video_id,
                        "video_title": info_dict.get('title', 'Unknown'),
                        "timestamp": target_seconds,
                        "timestamp_formatted": timestamp,
                        "output_path": str(output_file),
                        "resolution": f"{frame.shape[1]}x{frame.shape[0]}",
                        "quality_used": f"{selected_format.get('height', 'unknown')}p"
                    }
                    
                else:  # base64
                    # Encode image to base64
                    if image_format == "jpg":
                        _, buffer = cv2.imencode('.jpg', frame,
                                               [cv2.IMWRITE_JPEG_QUALITY, 95])
                    else:  # png
                        _, buffer = cv2.imencode('.png', frame)
                    
                    image_base64 = base64.b64encode(buffer).decode('utf-8')
                    
                    return {
                        "success": True,
                        "video_id": video_id,
                        "video_title": info_dict.get('title', 'Unknown'),
                        "timestamp": target_seconds,
                        "timestamp_formatted": timestamp,
                        "image_data": image_base64,
                        "image_format": image_format,
                        "resolution": f"{frame.shape[1]}x{frame.shape[0]}",
                        "quality_used": f"{selected_format.get('height', 'unknown')}p"
                    }
                    
        except Exception as e:
            return {
                "error": f"Unexpected error: {type(e).__name__}",
                "details": str(e)
            }
