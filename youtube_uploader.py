"""youtube_uploader.py — Upload videos to YouTube using Data API v3."""
import os
import pickle
from pathlib import Path
import config

TOKEN_PATH = Path(__file__).parent / "token.pickle"
CLIENT_SECRETS_PATH = Path(__file__).parent / "client_secrets.json"

def _get_credentials():
    """Get or refresh YouTube OAuth2 credentials."""
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    creds = None
    if TOKEN_PATH.exists():
        with open(TOKEN_PATH, "rb") as f:
            creds = pickle.load(f)
    if creds and creds.valid:
        return creds
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        if not CLIENT_SECRETS_PATH.exists():
            raise FileNotFoundError(
                "client_secrets.json not found. Download it from Google Cloud Console."
            )
        flow = InstalledAppFlow.from_client_secrets_file(
            str(CLIENT_SECRETS_PATH), config.YOUTUBE_SCOPES
        )
        creds = flow.run_local_server(port=0)
    with open(TOKEN_PATH, "wb") as f:
        pickle.dump(creds, f)
    return creds

def upload_video(video_path: str, title: str, description: str, tags: list = None,
                 category_id: str = "22", privacy: str = "private") -> dict:
    """Upload a video to YouTube."""
    try:
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
        if not os.path.exists(video_path):
            return {"success": False, "error": f"Video file not found: {video_path}"}
        creds = _get_credentials()
        youtube = build("youtube", "v3", credentials=creds)
        body = {
            "snippet": {
                "title": title[:100],
                "description": description[:5000],
                "tags": tags or [],
                "categoryId": category_id,
            },
            "status": {"privacyStatus": privacy}
        }
        media = MediaFileUpload(video_path, chunksize=-1, resumable=True, mimetype="video/mp4")
        request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
        response = None
        while response is None:
            _, response = request.next_chunk()
        video_id = response.get("id", "")
        return {
            "success": True,
            "video_id": video_id,
            "url": f"https://www.youtube.com/watch?v={video_id}",
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
