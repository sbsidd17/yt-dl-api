from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel
import yt_dlp
import re
from typing import Optional
import os
import tempfile

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

# Embedded Netscape cookies
NETSCAPE_COOKIES = """# Netscape HTTP Cookie File
# http://curl.haxx.se/rfc/cookie_spec.html
# This is a generated file!  Do not edit.

.youtube.com	TRUE	/	FALSE	1791783098	HSID	AFbXNnuoQ38m_Isbf
.youtube.com	TRUE	/	TRUE	1791783098	SSID	AFL2ZkJmyWfDHkaOZ
.youtube.com	TRUE	/	FALSE	1791783098	APISID	nCO_x36hbH_spNK-/A3b9x-CuwQ3QTOlve
.youtube.com	TRUE	/	TRUE	1791783098	SAPISID	zCtKazkWDBFVUx4C/A5msKbJka5fNRD3r0
.youtube.com	TRUE	/	TRUE	1791783098	__Secure-1PAPISID	zCtKazkWDBFVUx4C/A5msKbJka5fNRD3r0
.youtube.com	TRUE	/	TRUE	1791783098	__Secure-3PAPISID	zCtKazkWDBFVUx4C/A5msKbJka5fNRD3r0
.youtube.com	TRUE	/	TRUE	1779869218	LOGIN_INFO	AFmmF2swRQIhAKL2Z2ZAax5R3zDe9Lk_CqWggt8BHqllF1U4JV6xUx_FAiAFgtC0x7g9I6FabrjcI6OCoxE79H0WLtY8-INoS1luvg:QUQ3MjNmeEpHNmNXNmpUSzc5OTYxblVBQmt4ZGlpSzhSdzBKSXRXYjZWZm93MDd4d1hLYUhjQ25lWWNqVEhnVjNpSFJtWlplMWtuejFtNl9md0IxOGlxSU1weGhxLVBYMXIwMGFVSmZOSEx2eGdKQkNJSF9MWV81QmZHMXFvRE01REtRZFNrUkRtX05HY2RTQ1E4ckZ3NGxubjlkZEtPMnFB
.youtube.com	TRUE	/	TRUE	1792528180	PREF	f6=40000000&tz=Asia.Calcutta&f7=100&f4=4000000
.youtube.com	TRUE	/	FALSE	1791783098	SID	g.a0001Ajf9_sjTGl9s20zBSYrLp1NCEuoMyKesfzXCrzC6S3ldwBP5D_IRS3Ch3Lna9dX8YrMBAACgYKAccSARISFQHGX2Mil0mncc1gs6VWFsm1OiB-nhoVAUF8yKqApfPdXRnWUYUoHD9YRvtw0076
.youtube.com	TRUE	/	TRUE	1791783098	__Secure-1PSID	g.a0001Ajf9_sjTGl9s20zBSYrLp1NCEuoMyKesfzXCrzC6S3ldwBPA5iLiDjXgk_nMW4G9pUYQgACgYKAfsSARISFQHGX2Mi837Vtd11pI6pJk-yJyVFqxoVAUF8yKrU3_7LGxCQSJnQLXeHmN3I0076
.youtube.com	TRUE	/	TRUE	1791783098	__Secure-3PSID	g.a0001Ajf9_sjTGl9s20zBSYrLp1NCEuoMyKesfzXCrzC6S3ldwBPy21O0PkO_4ynQoX6L25caQACgYKATISARISFQHGX2MizUeedIFHFItzwAYbmHAjdBoVAUF8yKp0-EqNYqGw93ZpPnBzgOSo0076
.youtube.com	TRUE	/	TRUE	1789503590	__Secure-1PSIDTS	sidts-CjEBmkD5SwleRmts4iuiGj_Jf4GzzZeKXE9WskYk9h6iMOjST5srqUjInbA-44w6Eh5NEAA
.youtube.com	TRUE	/	TRUE	1789503590	__Secure-3PSIDTS	sidts-CjEBmkD5SwleRmts4iuiGj_Jf4GzzZeKXE9WskYk9h6iMOjST5srqUjInbA-44w6Eh5NEAA
.youtube.com	TRUE	/	FALSE	1757968186	ST-xuwub9	session_logininfo=AFmmF2swRQIhAKL2Z2ZAax5R3zDe9Lk_CqWggt8BHqllF1U4JV6xUx_FAiAFgtC0x7g9I6FabrjcI6OCoxE79H0WLtY8-INoS1luvg%3AQUQ3MjNmeEpHNmNXNmpUSzc5OTYxblVBQmt4ZGlpSzhSdzBKSXRXYjZWZm93MDd4d1hLYUhjQ25lWWNqVEhnVjNpSFJtWlplMWtuejFtNl9md0IxOGlxSU1weGhxLVBYMXIwMGFVSmZOSEx2eGdKQkNJSF9MWV81QmZHMXFvRE01REtRZFNrUkRtX05HY2RTQ1E4ckZ3NGxubjlkZEtPMnFB
.youtube.com	TRUE	/	FALSE	1789504183	SIDCC	AKEyXzXrH1cg1bIY0QUjtceOmSetHU4h0BjESHoeSFRVSF6Ok_7mujfcTp0z6IJ83IoU6QVu
.youtube.com	TRUE	/	TRUE	1789504183	__Secure-1PSIDCC	AKEyXzU7XZfZm4Miidc0tftMmXirK3WhAuZlVuJNqmnXyQp72I7HpNQgeakoy3RQ1jcSU-Wq3A
.youtube.com	TRUE	/	TRUE	1789504183	__Secure-3PSIDCC	AKEyXzWwqi5jMu96s5XbXZONUAyF2z51yVWTxo2Ksj2ubksXEPWgbEb0kg7_MNSuFkx9uA1X
"""

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

        # Write cookies to a temporary file
        cookie_file = None
        if NETSCAPE_COOKIES:
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as temp_cookie_file:
                temp_cookie_file.write(NETSCAPE_COOKIES)
                cookie_file = temp_cookie_file.name

        ydl_opts = {
            "format": "best[ext=mp4]/best",  # Prioritize MP4, fallback to best available
            "quiet": True,
            "geo_bypass": True,
            "nocheckcertificate": True,
            "ignoreerrors": True,
            "noprogress": True,
            "sleep_interval": 1,
            "youtube_include_dash_manifest": False,
            "cookiefile": cookie_file if cookie_file else None,  # Use temp file if cookies exist
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
