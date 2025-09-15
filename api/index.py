from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel
import yt_dlp
import re
from typing import Optional
import os
import tempfile
import requests  # Added for fetching GitHub raw link

app = FastAPI(
    title="YouTube Downloader API",
    description="API to extract direct download links for YouTube videos",
    version="1.0.0"
)

# Response model for download endpoint
class VideoResponse(BaseModel):
    title: str
    download_url: str
    format: str
    resolution: Optional[str] = None

class ErrorResponse(BaseModel):
    error: str

# GitHub raw link for cookies.txt
COOKIES_URL = "https://raw.githubusercontent.com/sbsidd17/yt-dl-api/refs/heads/main/api/cookies.txt"

@app.get("/", summary="API Welcome Message")
async def home():
    return {"message": "Welcome to YouTube Downloader API. Use /download?url=<YouTube_URL> to get video links."}

@app.get("/download", response_model=VideoResponse, responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
async def download_video(url: str = Query(..., title="YouTube Video URL", description="Valid YouTube video or shorts URL")):
    """
    Extract direct download link for a YouTube video.
    
    Args:
        url: YouTube video URL (e.g., https://www.youtube.com/watch?v=VIDEO_ID or https://youtu.be/VIDEO_ID)
    
    Returns:
        VideoResponse: Contains video title, direct download URL, format, and resolution
    """
    try:
        # Fix YouTube Shorts or other URL formats
        video_id_match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", url)
        if not video_id_match:
            raise HTTPException(status_code=400, detail="Invalid YouTube URL")
        url = f"https://www.youtube.com/watch?v={video_id_match.group(1)}"

        # Fetch cookies from GitHub raw link
        cookie_file = None
        try:
            response = requests.get(COOKIES_URL, timeout=5)
            response.raise_for_status()  # Raise exception for bad status codes
            cookies_content = response.text
            if cookies_content:
                # Write cookies to a temporary file
                with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as temp_cookie_file:
                    temp_cookie_file.write(cookies_content)
                    cookie_file = temp_cookie_file.name
        except requests.RequestException as e:
            # Log error but proceed without cookies
            print(f"Failed to fetch cookies: {str(e)}")

        ydl_opts = {
            "format": "best[ext=mp4]/best",  # Prioritize MP4, fallback to best available
            "quiet": True,
            "geo_bypass": True,
            "nocheckcertificate": True,
            "ignoreerrors": True,
            "noprogress": True,
            "sleep_interval": 1,
            "youtube_include_dash_manifest": False,
            "cookiefile": cookie_file if cookie_file else None,  # Use temp file if cookies fetched
            "headers": {
                "User-Agent": "Mozilla/5.0 (Linux; Android 10; SM-G975F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Mobile Safari/537.36",
                "Accept-Language": "en-US,en;q=0.5",
            },
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)

        # Clean up temporary cookie file if it was created
        if cookie_file and os.path.exists(cookie_file):
            os.remove(cookie_file)

        if not info_dict or "url" not in info_dict:
            raise HTTPException(status_code=400, detail="Failed to retrieve video info or video unavailable")

        return {
            "title": info_dict.get("title", "Unknown"),
            "download_url": info_dict["url"],
            "format": info_dict.get("ext", "mp4"),
            "resolution": info_dict.get("resolution", "Unknown")
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
