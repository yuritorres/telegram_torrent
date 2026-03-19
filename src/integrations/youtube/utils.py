from urllib.parse import urlparse


def format_duration(seconds: int) -> str:
    if not seconds:
        return "0s"
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes}m {secs}s"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"


def format_filesize(bytes_size: int) -> str:
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} TB"


def is_youtube_url(url: str) -> bool:
    youtube_domains = ['youtube.com', 'www.youtube.com', 'youtu.be', 'm.youtube.com']
    try:
        parsed = urlparse(url.lower())
        return any(domain in parsed.netloc for domain in youtube_domains)
    except Exception:
        return False
