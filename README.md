# YouTube Downloader API

A FastAPI-based API to extract direct download links for YouTube videos using `yt-dlp`. Deployable on Vercel.

## Features
- Extract direct MP4 download links for YouTube videos (including Shorts).
- Supports multiple resolutions (best available MP4 prioritized).
- Handles age-restricted or geo-blocked videos with optional cookies.
- OpenAPI documentation available at `/docs`.

## Prerequisites
- Python 3.8+
- Vercel CLI (`npm install -g vercel`)
- (Optional) YouTube cookies for restricted videos

## Setup
1. **Clone the repository**:
   ```bash
   git clone <your-repo-url>
   cd yt-dl-api
