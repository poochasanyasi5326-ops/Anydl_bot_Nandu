import re

YOUTUBE_REGEX = r"(https?://)?(www\.)?(youtube\.com|youtu\.be)/"

def is_youtube(url: str) -> bool:
    return re.search(YOUTUBE_REGEX, url) is not None
