"""
YouTube Video Downloader

This script can be used in two ways:
1. As a command-line tool to download YouTube videos directly from your terminal.
2. As a Python module to integrate video downloading capabilities into your own scripts.

--------------------------
Command-Line Usage
--------------------------
To run this script from your terminal:
1. Ensure you have Python installed.
2. Install the required library: pip install pytube
3. Execute the script:
   python youtube_downloader.py <YOUTUBE_VIDEO_URL> [OPTIONS]

Example:
   python youtube_downloader.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ" -o my_videos

Arguments for CLI:
  url         The full URL of the YouTube video to download (required).
  -o, --output  Optional. The directory where the video will be saved. 
                Defaults to the current directory if not specified.
  -r, --resolution Optional. Desired video resolution (e.g., "720p", "1080p").
                Note: Currently, the script downloads the highest available 
                progressive stream (video and audio combined) regardless of 
                this option. Full resolution selection is a future enhancement.

--------------------------
Using as a Module
--------------------------
You can import the `download_video` function into your own Python scripts.

Function:
  download_video(video_url: str, output_path: str = ".")
    Downloads a YouTube video to the specified path.
    Returns a tuple (success: bool, file_path_or_error: str | None).
    On success, (True, file_path).
    On failure, re-raises specific exceptions (RegexMatchError, VideoUnavailable, 
    URLError) or returns (False, error_message_string) for other issues.

Example of module usage:

from youtube_downloader import download_video
from pytube.exceptions import RegexMatchError, VideoUnavailable
import urllib.error
import os

if __name__ == "__main__": # This example part is illustrative for module use
    sample_url = "https://www.youtube.com/watch?v=your_video_id" # Replace with a real URL for testing
    download_directory = "downloaded_videos"
    os.makedirs(download_directory, exist_ok=True) # Ensure directory exists

    print(f"Attempting to download '{sample_url}' to '{download_directory}' using imported function.")

    try:
        success, result = download_video(sample_url, download_directory)
        if success:
            print(f"Module usage: Download successful! Video saved to: {result}")
        else:
            print(f"Module usage: Download failed. Reason: {result}")
    except RegexMatchError:
        print("Module usage: Invalid YouTube URL format.")
    except VideoUnavailable:
        print("Module usage: Video is unavailable (private, deleted, or restricted).")
    except urllib.error.URLError as e:
        print(f"Module usage: Network error. Details: {e.reason}")
    except Exception as e:
        print(f"Module usage: An unexpected error occurred: {e}")
"""
import argparse
from pytube import YouTube
from pytube.exceptions import RegexMatchError, VideoUnavailable
import os
import urllib.error # For network errors


def download_video(video_url: str, output_path: str = "."):
    """
    Downloads a YouTube video to the specified path. (This is the function docstring, not the module one)
    Returns a tuple (success: bool, file_path_or_error: str | None).
    On success, (True, file_path).
    On failure, re-raises specific exceptions or returns (False, error_message_string).
    """
    try:
        yt = YouTube(video_url)
        # This print can stay as it's useful info even for library use
        print(f"Fetching video: {yt.title}")

        streams = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc()

        if not streams:
            # This specific error is better handled by returning False and a message
            # rather than a custom exception, or the caller can check the stream list themselves.
            # For this refactor, we'll make it a return False.
            print("Error: No progressive MP4 streams found for this video.")
            return False, "No progressive MP4 streams found."

        selected_stream = streams.first()
        if not selected_stream: # Should not happen if streams is not empty
            print("Error: Could not select a video stream.")
            return False, "Could not select a video stream."
        
        # This print can also stay
        print(f"Selected stream: {selected_stream.resolution}, {selected_stream.mime_type}")

        if output_path != ".":
            os.makedirs(output_path, exist_ok=True)
        
        file_path = selected_stream.download(output_path=output_path)
        # Removed direct success print, will be handled by caller
        return True, file_path

    except RegexMatchError as e:
        print(f"Error: Invalid YouTube URL format. Details: {e}")
        raise # Re-raise for the caller to handle specifically
    except VideoUnavailable as e:
        print(f"Error: Video is unavailable. Details: {e}")
        raise # Re-raise
    except urllib.error.URLError as e:
        print(f"Error: Network issue. Details: {e.reason}")
        raise # Re-raise
    except FileNotFoundError as e: # This could happen if output_path becomes invalid after check
        print(f"Error: Invalid output path. Details: {e}")
        return False, str(e) # Return False as it's a runtime path issue
    except Exception as e:
        print(f"An unexpected error occurred during download: {e}")
        # For truly unexpected errors, returning False, str(e) is safer than re-raising generic Exception
        return False, str(e)


# CLI execution part starts here, separate from the module docstring.
if __name__ == "__main__":
    # The example of module usage in the docstring is illustrative.
    # The actual CLI parsing and execution logic remains below.
    
    parser = argparse.ArgumentParser(
        description="Download YouTube videos from the command line.",
        formatter_class=argparse.RawTextHelpFormatter 
    )
    parser.add_argument(
        "url", 
        help="The full URL of the YouTube video (e.g., \"https://www.youtube.com/watch?v=dQw4w9WgXcQ\")"
    )
    parser.add_argument(
        "-o", "--output", 
        default=".", 
        help="Output directory for the downloaded video.\nDefaults to the current directory."
    )
    parser.add_argument(
        "-r", "--resolution", 
        help="Desired video resolution (e.g., \"720p\", \"1080p\").\nNote: Currently selects the highest available progressive stream.\nFull resolution selection is a future enhancement."
    )

    args = parser.parse_args()
        
    try:
        print(f"Attempting to download: {args.url} (CLI mode)")
        if args.output != ".":
            print(f"Output directory: {os.path.abspath(args.output)}")
        if args.resolution:
            print(f"Requested resolution: {args.resolution} (Note: currently selects highest progressive)")

        success, result_path_or_msg = download_video(args.url, args.output)

        if success:
            print(f"\nDownload successful!")
            print(f"Video saved to: {result_path_or_msg}")
        else:
            print(f"\nDownload failed. Reason: {result_path_or_msg}")

    except RegexMatchError:
        print("CLI: Invalid YouTube URL format. Please check and try again.")
    except VideoUnavailable:
        print("CLI: This video may be private, deleted, or geo-restricted.")
    except urllib.error.URLError:
        print("CLI: Network error. Please check your internet connection.")
    except Exception as e: 
        print(f"CLI: An unexpected error occurred: {e}")
