#!/usr/bin/env python3
"""Worker script for uploading videos to YouTube in the background"""

import os
import sys
import json
import time
import argparse
import signal
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload


class UploadWorker:
    """Handles YouTube video upload with progress tracking"""
    
    def __init__(self, session_id: str, state_dir: str):
        self.session_id = session_id
        self.state_dir = Path(state_dir)
        self.state_file = self.state_dir / f"{session_id}.json"
        self.interrupted = False
        
        # Set up signal handlers
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle termination signals"""
        self.interrupted = True
        self._update_state({"status": "cancelled", "error": "Upload interrupted"})
        sys.exit(0)
    
    def _read_state(self) -> Dict[str, Any]:
        """Read current state from file"""
        try:
            with open(self.state_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error reading state: {e}")
            return {}
    
    def _update_state(self, updates: Dict[str, Any]):
        """Update state file with new values"""
        state = self._read_state()
        state.update(updates)
        state["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        try:
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            print(f"Error updating state: {e}")
    
    def _build_youtube_service(self, client_secrets_file: str, token_file: str):
        """Build YouTube API service with OAuth credentials"""
        try:
            # Load credentials from token file
            if not os.path.exists(token_file):
                raise Exception(f"Token file not found: {token_file}")
            
            creds = Credentials.from_authorized_user_file(token_file, 
                ['https://www.googleapis.com/auth/youtube.upload'])
            
            # Build the service
            return build('youtube', 'v3', credentials=creds)
        except Exception as e:
            self._update_state({"status": "failed", "error": f"Auth error: {str(e)}"})
            raise
    
    def _resumable_upload(self, service, file_path: str, body: dict) -> Optional[str]:
        """Upload video using resumable upload protocol"""
        
        # Create media upload object
        media = MediaFileUpload(
            file_path,
            mimetype='video/*',
            resumable=True,
            chunksize=1024*1024  # 1MB chunks
        )
        
        # Create the request
        request = service.videos().insert(
            part=",".join(body.keys()),
            body=body,
            media_body=media
        )
        
        response = None
        error = None
        retry = 0
        
        while response is None:
            try:
                status, response = request.next_chunk()
                
                if status:
                    # Update progress
                    progress = status.progress()
                    bytes_uploaded = int(status.total_size * progress)
                    
                    self._update_state({
                        "progress": progress,
                        "bytes_uploaded": bytes_uploaded,
                        "status": "uploading"
                    })
                    
                    # Check for interruption
                    if self.interrupted:
                        return None
                
            except HttpError as e:
                if e.resp.status in [500, 502, 503, 504]:
                    # Retry on server errors
                    error = f"Server error: {e}"
                    retry += 1
                    if retry > 5:
                        raise
                    time.sleep(2 ** retry)
                else:
                    raise
            
            except Exception as e:
                # Resumable upload supports recovery
                error = f"Upload error: {e}"
                retry += 1
                if retry > 3:
                    raise
                time.sleep(5)
        
        if response and 'id' in response:
            return response['id']
        return None
    
    def upload(self, args):
        """Main upload process"""
        try:
            # Update status
            self._update_state({"status": "processing", "error": None})
            
            # Build YouTube service
            youtube = self._build_youtube_service(args.client_secrets, args.token_file)
            
            # Prepare video metadata
            body = {
                'snippet': {
                    'title': args.title,
                    'description': args.description,
                },
                'status': {
                    'privacyStatus': args.privacy_status,
                    'selfDeclaredMadeForKids': False
                }
            }
            
            # Add optional fields
            if args.category_id:
                body['snippet']['categoryId'] = args.category_id
            
            if args.tags:
                body['snippet']['tags'] = args.tags.split(',')
            
            # Start upload
            self._update_state({"status": "uploading"})
            
            video_id = self._resumable_upload(youtube, args.file_path, body)
            
            if video_id:
                # Success!
                self._update_state({
                    "status": "completed",
                    "video_id": video_id,
                    "progress": 1.0,
                    "bytes_uploaded": os.path.getsize(args.file_path),
                    "completed_at": datetime.now(timezone.utc).isoformat()
                })
                print(f"Upload completed: {video_id}")
            else:
                self._update_state({
                    "status": "failed",
                    "error": "Upload failed - no video ID returned"
                })
                
        except Exception as e:
            self._update_state({
                "status": "failed",
                "error": str(e)
            })
            print(f"Upload failed: {e}")
            sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description='YouTube Video Upload Worker')
    parser.add_argument('--session-id', required=True, help='Upload session ID')
    parser.add_argument('--state-dir', required=True, help='State directory path')
    parser.add_argument('--file-path', required=True, help='Video file path')
    parser.add_argument('--title', required=True, help='Video title')
    parser.add_argument('--description', default='', help='Video description')
    parser.add_argument('--tags', default='', help='Comma-separated tags')
    parser.add_argument('--category-id', default=None, help='YouTube category ID (optional)')
    parser.add_argument('--privacy-status', default='private', 
                       choices=['private', 'unlisted', 'public'])
    parser.add_argument('--client-secrets', default='client_secrets.json',
                       help='OAuth client secrets file')
    parser.add_argument('--token-file', default='token.json',
                       help='OAuth token file')
    
    args = parser.parse_args()
    
    # Create worker and start upload
    worker = UploadWorker(args.session_id, args.state_dir)
    worker.upload(args)


if __name__ == '__main__':
    main()