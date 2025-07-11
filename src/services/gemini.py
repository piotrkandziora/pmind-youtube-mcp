"""Gemini AI integration for YouTube video analysis"""

import os
from typing import Dict, Any, Annotated, Optional, List, Literal
from pydantic import Field
from fastmcp import FastMCP
from ..config import Config
import logging

logger = logging.getLogger(__name__)

from google import genai
from google.genai import types


def register_tools(mcp: FastMCP, config: Config):
    """Register Gemini-related tools with the MCP server"""
    
    def _get_gemini_client(model: Optional[str] = None) -> tuple[genai.Client, str]:
        """Helper function to create and return a Gemini client with model"""
        # Check if API key is configured
        if not config.gemini_api_key:
            raise ValueError("Gemini API key not configured. Set GEMINI_API_KEY environment variable.")
        
        # Determine model to use
        model_to_use = model or config.gemini_model
        
        # Create and return the client and the model being used
        return genai.Client(api_key=config.gemini_api_key), model_to_use
    
    @mcp.tool
    async def gemini_analyze_youtube_video(
        youtube_url: Annotated[str, Field(
            description="YouTube video URL (e.g., https://www.youtube.com/watch?v=VIDEO_ID)"
        )],
        prompt: Annotated[str, Field(
            description="What to analyze or extract from the video"
        )],
        model: Annotated[Optional[str], Field(
            default=None,
            description="Gemini model to use (defaults to GEMINI_MODEL env var)"
        )] = None
    ) -> Dict[str, Any]:
        """
        Analyze a YouTube video using Google's Gemini AI.
        
        Capabilities:
        - Transcribe audio content
        - Provide visual descriptions
        - Summarize video content
        - Answer questions about specific timestamps
        - Extract information from the video
        
        Note: Only works with public YouTube videos.
        Free tier limit: 8 hours of video per day.
        """
        try:
            # Get client and model
            client, model_to_use = _get_gemini_client(model)
            
            # Generate content with YouTube URL
            response = client.models.generate_content(
                model=f"models/{model_to_use}",
                contents=types.Content(
                    parts=[
                        types.Part(
                            file_data=types.FileData(file_uri=youtube_url)
                        ),
                        types.Part(text=prompt)
                    ]
                )
            )
            
            return {
                "success": True,
                "youtube_url": youtube_url,
                "prompt": prompt,
                "model": model_to_use,
                "response": response.text,
                "usage": {
                    "prompt_tokens": getattr(response.usage_metadata, 'prompt_token_count', None) if hasattr(response, 'usage_metadata') else None,
                    "completion_tokens": getattr(response.usage_metadata, 'candidates_token_count', None) if hasattr(response, 'usage_metadata') else None,
                    "total_tokens": getattr(response.usage_metadata, 'total_token_count', None) if hasattr(response, 'usage_metadata') else None
                }
            }
            
        except ValueError as e:
            return {
                "error": str(e)
            }
        except Exception as e:
            return {
                "error": f"Gemini API error: {str(e)}",
                "type": type(e).__name__
            }
    
    @mcp.tool
    async def gemini_compare_youtube_videos(
        youtube_urls: Annotated[List[str], Field(
            description="List of YouTube video URLs to compare (max 10 for Gemini 2.5+)",
            min_length=2,
            max_length=10
        )],
        comparison_prompt: Annotated[str, Field(
            description="How to compare the videos (e.g., 'Compare the main topics discussed')"
        )],
        model: Annotated[Optional[str], Field(
            default=None,
            description="Gemini model to use (defaults to GEMINI_MODEL env var)"
        )] = None
    ) -> Dict[str, Any]:
        """
        Compare multiple YouTube videos using Gemini AI.
        
        Useful for:
        - Comparing content across videos
        - Finding similarities and differences
        - Analyzing multiple perspectives on a topic
        - Summarizing a video series
        
        Note: Models 2.5+ support up to 10 videos per request.
        Earlier models only support 1 video at a time.
        """
        try:
            # Get client and model
            client, model_to_use = _get_gemini_client(model)
            
            # Build content parts with all videos and the prompt
            parts = []
            for url in youtube_urls:
                parts.append(types.Part(
                    file_data=types.FileData(file_uri=url)
                ))
            parts.append(types.Part(text=comparison_prompt))
            
            # Generate comparison
            response = client.models.generate_content(
                model=f"models/{model_to_use}",
                contents=types.Content(parts=parts)
            )
            
            return {
                "success": True,
                "youtube_urls": youtube_urls,
                "comparison_prompt": comparison_prompt,
                "model": model_to_use,
                "response": response.text,
                "video_count": len(youtube_urls),
                "usage": {
                    "prompt_tokens": response.usage_metadata.prompt_token_count if hasattr(response, 'usage_metadata') else None,
                    "completion_tokens": response.usage_metadata.candidates_token_count if hasattr(response, 'usage_metadata') else None,
                    "total_tokens": response.usage_metadata.total_token_count if hasattr(response, 'usage_metadata') else None
                }
            }
            
        except Exception as e:
            return {
                "error": f"Gemini API error: {str(e)}",
                "type": type(e).__name__
            }
    
    @mcp.tool
    async def gemini_video_qa(
        youtube_url: Annotated[str, Field(
            description="YouTube video URL"
        )],
        questions: Annotated[List[str], Field(
            description="List of questions to ask about the video",
            min_length=1,
            max_length=10
        )],
        model: Annotated[Optional[str], Field(
            default=None,
            description="Gemini model to use (defaults to GEMINI_MODEL env var)"
        )] = None,
        include_timestamps: Annotated[bool, Field(
            default=False,
            description="Request timestamps for answers when relevant"
        )] = False
    ) -> Dict[str, Any]:
        """
        Ask multiple questions about a YouTube video.
        
        Useful for:
        - Extracting specific information
        - Understanding video content at specific timestamps
        - Getting detailed explanations about video segments
        - Fact-checking or verification
        
        The model can reference specific timestamps when answering.
        """
        try:
            # Get client and model
            client, model_to_use = _get_gemini_client(model)
            
            # Format questions
            formatted_questions = "\n".join([f"{i+1}. {q}" for i, q in enumerate(questions)])
            
            prompt = f"Please answer the following questions about this video:\n\n{formatted_questions}"
            
            if include_timestamps:
                prompt += "\n\nWhen relevant, include timestamps (MM:SS format) for your answers."
            
            # Generate answers
            response = client.models.generate_content(
                model=f"models/{model_to_use}",
                contents=types.Content(
                    parts=[
                        types.Part(
                            file_data=types.FileData(file_uri=youtube_url)
                        ),
                        types.Part(text=prompt)
                    ]
                )
            )
            
            return {
                "success": True,
                "youtube_url": youtube_url,
                "questions": questions,
                "model": model_to_use,
                "include_timestamps": include_timestamps,
                "response": response.text,
                "usage": {
                    "prompt_tokens": getattr(response.usage_metadata, 'prompt_token_count', None) if hasattr(response, 'usage_metadata') else None,
                    "completion_tokens": getattr(response.usage_metadata, 'candidates_token_count', None) if hasattr(response, 'usage_metadata') else None,
                    "total_tokens": getattr(response.usage_metadata, 'total_token_count', None) if hasattr(response, 'usage_metadata') else None
                }
            }
            
        except Exception as e:
            return {
                "error": f"Gemini API error: {str(e)}",
                "type": type(e).__name__
            }
    
    @mcp.tool
    async def gemini_video_transcript(
        youtube_url: Annotated[str, Field(
            description="YouTube video URL to transcribe"
        )],
        model: Annotated[Optional[str], Field(
            default=None,
            description="Gemini model to use (defaults to GEMINI_MODEL env var)"
        )] = None,
        include_timestamps: Annotated[bool, Field(
            default=True,
            description="Include timestamps in the transcript"
        )] = True,
        format: Annotated[Literal["text", "srt", "segments"], Field(
            default="text",
            description="Output format for the transcript"
        )] = "text"
    ) -> Dict[str, Any]:
        """
        Generate a transcript of a YouTube video using Gemini.
        
        This uses Gemini's ability to understand both audio and visual content,
        providing a more comprehensive transcript than audio-only services.
        
        Output formats:
        - text: Plain text transcript
        - srt: SubRip subtitle format
        - segments: Timestamped segments
        """
        try:
            # Get client and model
            client, model_to_use = _get_gemini_client(model)
            
            # Build prompt based on format
            if format == "srt":
                prompt = "Generate a complete transcript of this video in SRT subtitle format with accurate timestamps."
            elif format == "segments":
                prompt = "Generate a transcript of this video with timestamps for each segment or speaker turn. Format: [MM:SS] Text"
            else:
                if include_timestamps:
                    prompt = "Generate a complete transcript of this video. Include timestamps [MM:SS] at regular intervals or scene changes."
                else:
                    prompt = "Generate a complete transcript of this video as continuous text without timestamps."
            
            # Generate transcript
            response = client.models.generate_content(
                model=f"models/{model_to_use}",
                contents=types.Content(
                    parts=[
                        types.Part(
                            file_data=types.FileData(file_uri=youtube_url)
                        ),
                        types.Part(text=prompt)
                    ]
                )
            )
            
            return {
                "success": True,
                "youtube_url": youtube_url,
                "model": model_to_use,
                "format": format,
                "include_timestamps": include_timestamps,
                "transcript": response.text,
                "usage": {
                    "prompt_tokens": response.usage_metadata.prompt_token_count if hasattr(response, 'usage_metadata') else None,
                    "completion_tokens": response.usage_metadata.candidates_token_count if hasattr(response, 'usage_metadata') else None,
                    "total_tokens": response.usage_metadata.total_token_count if hasattr(response, 'usage_metadata') else None
                }
            }
            
        except Exception as e:
            return {
                "error": f"Gemini API error: {str(e)}",
                "type": type(e).__name__
            }