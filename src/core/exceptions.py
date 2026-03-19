class TelegramTorrentError(Exception):
    """Base exception for this project."""


class QBittorrentError(TelegramTorrentError):
    """Raised when qBittorrent operations fail."""


class JellyfinError(TelegramTorrentError):
    """Raised when Jellyfin operations fail."""


class WhatsAppError(TelegramTorrentError):
    """Raised when WhatsApp/WAHA operations fail."""


class YouTubeError(TelegramTorrentError):
    """Raised when YouTube download operations fail."""


class UnauthorizedError(TelegramTorrentError):
    """Raised when a user is not authorized."""
