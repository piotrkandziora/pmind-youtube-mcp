"""Transcript-related MCP tools"""

from typing import Dict, Any, Optional, Annotated
from pydantic import Field
from fastmcp import FastMCP
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from ..config import Config


def register_tools(mcp: FastMCP, config: Config):
    """Register transcript-related tools with the MCP server"""
    
    @mcp.tool
    async def transcripts_get_transcript(
        video_id: Annotated[str, Field(description="The YouTube video ID")],
        language: Annotated[Optional[str], Field(
            default=None,
            description="Language code for the transcript (e.g., 'en', 'es', 'fr')"
        )] = None
    ) -> Dict[str, Any]:
        """Get the transcript of a YouTube video (no API key required)"""
        try:
            # Use configured language if none specified
            target_language = language or config.raw_transcript_lang
            
            # Try to get transcript in specified language
            try:
                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                
                # Try to find transcript in target language
                try:
                    transcript = transcript_list.find_transcript([target_language])
                except:
                    # If target language not found, try to get any available transcript
                    # and translate it if possible
                    try:
                        transcript = transcript_list.find_generated_transcript([target_language])
                    except:
                        # Get the first available transcript
                        transcript = next(iter(transcript_list))
                        if target_language != transcript.language_code:
                            # Try to translate to target language
                            try:
                                transcript = transcript.translate(target_language)
                            except:
                                pass  # Use original if translation fails
                
                # Fetch the actual transcript
                transcript_data = transcript.fetch()
                
                # Format transcript entries
                formatted_transcript = []
                for entry in transcript_data:
                    formatted_transcript.append({
                        "text": entry.text,
                        "start": entry.start,
                        "duration": entry.duration
                    })
                
                # Create full text version
                full_text = " ".join([entry.text for entry in transcript_data])
                
                return {
                    "videoId": video_id,
                    "language": transcript.language_code,
                    "languageName": transcript.language,
                    "isGenerated": transcript.is_generated,
                    "isTranslated": transcript.is_translatable,
                    "transcript": formatted_transcript,
                    "fullText": full_text
                }
                
            except TranscriptsDisabled:
                return {
                    "error": f"Transcripts are disabled for video '{video_id}'"
                }
            except NoTranscriptFound:
                return {
                    "error": f"No transcript found for video '{video_id}' in language '{target_language}'"
                }
            
        except ValueError as e:
            if "Video unavailable" in str(e):
                return {
                    "error": f"Video with ID '{video_id}' is unavailable or does not exist"
                }
            return {
                "error": f"Invalid video ID: {str(e)}"
            }
        except Exception as e:
            return {
                "error": f"Failed to fetch transcript: {str(e)}"
            }