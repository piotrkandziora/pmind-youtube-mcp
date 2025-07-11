"""Upload Manager for handling background YouTube video uploads"""

import os
import json
import time
import subprocess
import signal
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid
import psutil


class UploadManager:
    """Manages background video upload processes"""
    
    def __init__(self, state_dir: str = "/tmp/yt-uploads"):
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        
    def _get_state_file(self, session_id: str) -> Path:
        """Get path to state file for a session"""
        return self.state_dir / f"{session_id}.json"
    
    def _read_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Read state from file"""
        state_file = self._get_state_file(session_id)
        if state_file.exists():
            try:
                with open(state_file, 'r') as f:
                    return json.load(f)
            except Exception:
                return None
        return None
    
    def _write_state(self, session_id: str, state: Dict[str, Any]):
        """Write state to file"""
        state_file = self._get_state_file(session_id)
        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2)
    
    def _is_process_running(self, pid: int) -> bool:
        """Check if a process is still running"""
        try:
            # Check if process exists
            os.kill(pid, 0)
            # Verify it's actually our upload process
            try:
                proc = psutil.Process(pid)
                cmdline = ' '.join(proc.cmdline())
                return 'upload_worker.py' in cmdline
            except:
                return True  # Process exists but can't verify, assume it's ours
        except OSError:
            return False
    
    def start_upload(
        self,
        file_path: str,
        title: str,
        description: str = "",
        tags: List[str] = None,
        category_id: Optional[str] = None,
        privacy_status: str = "private",
        client_secrets_file: str = "client_secrets.json",
        token_file: str = "token.json"
    ) -> Dict[str, Any]:
        """Start a new upload process"""
        
        # Validate file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Video file not found: {file_path}")
        
        # Generate session ID
        session_id = f"upload_{uuid.uuid4().hex[:8]}_{int(time.time())}"
        
        # Create initial state
        file_size = os.path.getsize(file_path)
        state = {
            "session_id": session_id,
            "video_id": "pending",
            "status": "starting",
            "progress": 0.0,
            "bytes_uploaded": 0,
            "total_bytes": file_size,
            "file_path": file_path,
            "title": title,
            "description": description,
            "tags": tags or [],
            "category_id": category_id,
            "privacy_status": privacy_status,
            "started_at": datetime.utcnow().isoformat() + "Z",
            "updated_at": datetime.utcnow().isoformat() + "Z",
            "pid": None,
            "error": None
        }
        
        # Save initial state
        self._write_state(session_id, state)
        
        # Prepare command
        worker_script = Path(__file__).parent / "upload_worker.py"
        cmd = [
            "python", str(worker_script),
            "--session-id", session_id,
            "--state-dir", str(self.state_dir),
            "--file-path", file_path,
            "--title", title,
            "--description", description,
            "--privacy-status", privacy_status,
            "--client-secrets", client_secrets_file,
            "--token-file", token_file
        ]
        
        if category_id:
            cmd.extend(["--category-id", category_id])
        
        if tags:
            cmd.extend(["--tags", ",".join(tags)])
        
        # Start subprocess
        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True  # Detach from parent process group
            )
            
            # Update state with PID
            state["pid"] = proc.pid
            state["status"] = "uploading"
            self._write_state(session_id, state)
            
            return {
                "session_id": session_id,
                "status": "started",
                "pid": proc.pid,
                "file_size": file_size
            }
            
        except Exception as e:
            state["status"] = "failed"
            state["error"] = str(e)
            self._write_state(session_id, state)
            raise
    
    def get_status(self, session_id: str) -> Dict[str, Any]:
        """Get status of an upload"""
        state = self._read_state(session_id)
        
        if not state:
            return {
                "error": "Upload session not found",
                "session_id": session_id
            }
        
        # Check if process is still running
        if state.get("pid") and state["status"] in ["uploading", "processing"]:
            if not self._is_process_running(state["pid"]):
                # Process died unexpectedly
                if state["status"] != "completed" and not state.get("error"):
                    state["status"] = "failed"
                    state["error"] = "Upload process terminated unexpectedly"
                    self._write_state(session_id, state)
        
        # Calculate upload rate if in progress
        if state["status"] == "uploading" and state["progress"] > 0:
            elapsed = (datetime.utcnow() - datetime.fromisoformat(state["started_at"].rstrip("Z"))).total_seconds()
            if elapsed > 0:
                upload_rate = state["bytes_uploaded"] / elapsed  # bytes per second
                remaining_bytes = state["total_bytes"] - state["bytes_uploaded"]
                eta_seconds = remaining_bytes / upload_rate if upload_rate > 0 else 0
                state["upload_rate_mbps"] = (upload_rate * 8) / (1024 * 1024)  # Mbps
                state["eta_seconds"] = int(eta_seconds)
        
        return state
    
    def list_uploads(self, active_only: bool = False) -> List[Dict[str, Any]]:
        """List all upload sessions"""
        uploads = []
        
        for state_file in self.state_dir.glob("upload_*.json"):
            session_id = state_file.stem
            state = self._read_state(session_id)
            
            if state:
                # Update status for running processes
                if state.get("pid") and state["status"] in ["uploading", "processing"]:
                    if not self._is_process_running(state["pid"]):
                        state["status"] = "failed" if state["status"] != "completed" else state["status"]
                
                if not active_only or state["status"] in ["uploading", "processing", "starting"]:
                    uploads.append(state)
        
        # Sort by start time, newest first
        uploads.sort(key=lambda x: x.get("started_at", ""), reverse=True)
        return uploads
    
    def cancel_upload(self, session_id: str) -> Dict[str, Any]:
        """Cancel an upload"""
        state = self._read_state(session_id)
        
        if not state:
            return {
                "error": "Upload session not found",
                "session_id": session_id
            }
        
        if state["status"] not in ["uploading", "processing", "starting"]:
            return {
                "error": f"Cannot cancel upload in status: {state['status']}",
                "session_id": session_id,
                "status": state["status"]
            }
        
        # Try to terminate the process
        if state.get("pid"):
            try:
                os.kill(state["pid"], signal.SIGTERM)
                time.sleep(1)  # Give it a moment to clean up
                
                # Force kill if still running
                if self._is_process_running(state["pid"]):
                    os.kill(state["pid"], signal.SIGKILL)
            except OSError:
                pass  # Process already dead
        
        # Update state
        state["status"] = "cancelled"
        state["error"] = "Cancelled by user"
        state["updated_at"] = datetime.utcnow().isoformat() + "Z"
        self._write_state(session_id, state)
        
        return {
            "session_id": session_id,
            "status": "cancelled",
            "message": "Upload cancelled successfully"
        }
    
    def cleanup_old_uploads(self, days: int = 7):
        """Clean up old upload state files"""
        cutoff_time = time.time() - (days * 24 * 60 * 60)
        cleaned = 0
        
        for state_file in self.state_dir.glob("upload_*.json"):
            if state_file.stat().st_mtime < cutoff_time:
                try:
                    state = self._read_state(state_file.stem)
                    # Only clean up completed/failed uploads
                    if state and state["status"] in ["completed", "failed", "cancelled"]:
                        state_file.unlink()
                        cleaned += 1
                except Exception:
                    pass
        
        return cleaned