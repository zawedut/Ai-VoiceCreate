
import os
import time
import uuid
import asyncio
import shutil
import logging
from typing import Optional, List
from pathlib import Path

from fastapi import FastAPI, BackgroundTasks, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

# Import modules
from config.settings import TEMP_DIR, OUTPUT_DIR, ensure_directories
from modules.downloader import download_single_video
from modules.gemini_brain import get_perfect_fit_script
from modules.voice import generate_voice_sync
from modules.video_processor import (
    resize_for_shorts, sync_audio_to_video, render_final_video,
    prepare_avatar_with_chromakey, cleanup_temp_files
)
from moviepy.editor import VideoFileClip, AudioFileClip
import google.generativeai as genai

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Video Factory API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage
tasks = {}

class VideoRequest(BaseModel):
    url: str
    custom_prompt: Optional[str] = None
    use_avatar: bool = True
    api_key: Optional[str] = None  # For Free mode

class TaskStatus(BaseModel):
    id: str
    status: str  # pending, processing, completed, failed
    progress: int
    message: str
    result_file: Optional[str] = None
    error: Optional[str] = None

def process_video_task(task_id: str, request: VideoRequest):
    """Background task logic"""
    try:
        tasks[task_id]["status"] = "processing"
        tasks[task_id]["progress"] = 10
        tasks[task_id]["message"] = "Downloading video..."
        
        # 0. Setup API Key
        if request.api_key:
            genai.configure(api_key=request.api_key)
        
        ensure_directories()
        
        # 1. Download
        video_path = download_single_video(request.url, TEMP_DIR)
        if not video_path:
            raise Exception("Download failed")
            
        tasks[task_id]["progress"] = 30
        tasks[task_id]["message"] = "Analyzing video & generating script..."
        
        # Get duration
        clip = VideoFileClip(video_path)
        duration = clip.duration
        clip.close()
        
        # 2. Generate Script
        # TODO: Support custom prompt injection if needed
        title, script = get_perfect_fit_script(video_path, duration)
        
        if not script:
             raise Exception("Failed to generate script")
             
        tasks[task_id]["progress"] = 50
        tasks[task_id]["message"] = "Generating voice..."
        
        # 3. Generate Voice
        voice_path = str(TEMP_DIR / f"voice_{task_id}.mp3")
        generate_voice_sync(script, voice_path)
        
        if not Path(voice_path).exists():
            raise Exception("Voice generation failed")
            
        tasks[task_id]["progress"] = 70
        tasks[task_id]["message"] = "Processing video (Rendering)..."
        
        # 4. Processing
        source_clip = VideoFileClip(video_path)
        audio_clip = AudioFileClip(voice_path)
        
        synced_audio = sync_audio_to_video(audio_clip, duration)
        synced_audio_path = TEMP_DIR / f"synced_{task_id}.mp3"
        synced_audio.write_audiofile(str(synced_audio_path), logger=None)
        final_audio = AudioFileClip(str(synced_audio_path))
        
        resized_clip = resize_for_shorts(source_clip)
        
        has_avatar = False
        if request.use_avatar:
            has_avatar = prepare_avatar_with_chromakey(duration)
            
        output_filename = f"final_{task_id}.mp4"
        output_path = OUTPUT_DIR / output_filename
        
        render_final_video(resized_clip, final_audio, output_path, add_avatar=has_avatar)
        
        # Cleanup
        source_clip.close()
        audio_clip.close()
        final_audio.close()
        
        # Remove temps
        cleanup_temp_files()
        
        tasks[task_id]["status"] = "completed"
        tasks[task_id]["progress"] = 100
        tasks[task_id]["message"] = "Done!"
        tasks[task_id]["result_file"] = output_filename
        
    except Exception as e:
        logger.error(f"Task failed: {e}")
        tasks[task_id]["status"] = "failed"
        tasks[task_id]["error"] = str(e)
        tasks[task_id]["message"] = "Error occurred"

@app.post("/api/process", response_model=TaskStatus)
async def create_process_task(request: VideoRequest, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    tasks[task_id] = {
        "id": task_id,
        "status": "pending",
        "progress": 0,
        "message": "Queued",
        "result_file": None
    }
    
    background_tasks.add_task(process_video_task, task_id, request)
    return tasks[task_id]

@app.get("/api/status/{task_id}", response_model=TaskStatus)
async def get_status(task_id: str):
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    return tasks[task_id]

@app.get("/api/download/{filename}")
async def download_file(filename: str):
    file_path = OUTPUT_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path, media_type="video/mp4", filename=filename)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
