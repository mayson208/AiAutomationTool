"""analytics.py — Fetch YouTube channel stats using Data API v3."""
import config

def get_channel_stats() -> dict:
    """Fetch views, subscribers, and watch time for the authenticated channel."""
    try:
        from googleapiclient.discovery import build
        import youtube_uploader
        creds = youtube_uploader._get_credentials()
        youtube = build("youtube", "v3", credentials=creds)
        # Get channel ID
        channels = youtube.channels().list(part="id,statistics,snippet", mine=True).execute()
        if not channels.get("items"):
            return {"success": False, "error": "No channel found for this account"}
        channel = channels["items"][0]
        stats = channel.get("statistics", {})
        return {
            "success": True,
            "channel_name": channel["snippet"]["title"],
            "channel_id": channel["id"],
            "subscribers": int(stats.get("subscriberCount", 0)),
            "total_views": int(stats.get("viewCount", 0)),
            "video_count": int(stats.get("videoCount", 0)),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_recent_videos(max_results: int = 10) -> dict:
    """Fetch recent videos with their view counts."""
    try:
        from googleapiclient.discovery import build
        import youtube_uploader
        creds = youtube_uploader._get_credentials()
        youtube = build("youtube", "v3", credentials=creds)
        search = youtube.search().list(
            part="snippet", forMine=True, type="video",
            order="date", maxResults=max_results
        ).execute()
        video_ids = [item["id"]["videoId"] for item in search.get("items", [])]
        if not video_ids:
            return {"success": True, "videos": []}
        stats = youtube.videos().list(
            part="snippet,statistics", id=",".join(video_ids)
        ).execute()
        videos = []
        for v in stats.get("items", []):
            s = v.get("statistics", {})
            videos.append({
                "title": v["snippet"]["title"],
                "video_id": v["id"],
                "url": f"https://www.youtube.com/watch?v={v['id']}",
                "views": int(s.get("viewCount", 0)),
                "likes": int(s.get("likeCount", 0)),
                "comments": int(s.get("commentCount", 0)),
                "published": v["snippet"]["publishedAt"][:10],
                "thumbnail": v["snippet"]["thumbnails"].get("medium", {}).get("url", ""),
            })
        return {"success": True, "videos": videos}
    except Exception as e:
        return {"success": False, "error": str(e)}
