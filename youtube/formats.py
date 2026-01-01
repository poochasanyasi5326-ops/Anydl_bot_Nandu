import yt_dlp

def get_formats(url):
    ydl = yt_dlp.YoutubeDL({"quiet": True})
    info = ydl.extract_info(url, download=False)
    return [
        (f["format_id"], f"{f['ext']} {f.get('height','?')}p")
        for f in info["formats"]
        if f.get("vcodec") != "none"
    ]
