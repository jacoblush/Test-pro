"""
Utility functions for the YouTube Shorts Auto-Clipper Bot.
"""

import os
import logging
from typing import List, Dict, Any, Tuple
import random
import numpy as np
from googleapiclient.discovery import build
from dotenv import load_dotenv
from pytube import YouTube

# Import moviepy dynamically to prevent import errors
try:
    from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False
    print("Warning: moviepy not available. Video editing functions will be limited.")

# Import OpenCV dynamically to prevent import errors
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("Warning: opencv-python not available. Video analysis will be limited.")

import config

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def create_youtube_client():
    """Create and return a YouTube API client."""
    youtube_api_key = os.getenv("YOUTUBE_API_KEY")
    if not youtube_api_key:
        raise ValueError("YouTube API key not found in environment variables")
    
    return build("youtube", "v3", developerKey=youtube_api_key)


def search_youtube_videos(
    query: str,
    max_results: int = config.YOUTUBE_MAX_RESULTS,
    order: str = config.DEFAULT_SEARCH_ORDER,
) -> List[Dict[str, Any]]:
    """
    Search for YouTube videos based on the given query.
    
    Args:
        query: Search query string
        max_results: Maximum number of results to return
        order: Order of results (default: by view count)
        
    Returns:
        List of video data dictionaries
    """
    try:
        youtube = create_youtube_client()
        
        # Map order string to YouTube API parameter
        order_param = config.YOUTUBE_SEARCH_CRITERIA.get(order, "viewCount")
        
        # Execute search request
        search_response = youtube.search().list(
            q=query,
            part="id,snippet",
            maxResults=max_results,
            order=order_param,
            type="video",
            videoDuration="medium",  # Medium videos (4-20 minutes)
        ).execute()
        
        # Extract video IDs for stats lookup
        video_ids = [item["id"]["videoId"] for item in search_response["items"]]
        
        if not video_ids:
            logger.warning("No videos found matching the search query")
            return []
        
        # Get video statistics
        videos_response = youtube.videos().list(
            id=",".join(video_ids),
            part="statistics,contentDetails,snippet",
        ).execute()
        
        # Combine search results with statistics
        videos_data = []
        for video in videos_response["items"]:
            video_data = {
                "id": video["id"],
                "title": video["snippet"]["title"],
                "channel": video["snippet"]["channelTitle"],
                "publish_date": video["snippet"]["publishedAt"],
                "description": video["snippet"]["description"],
                "view_count": int(video["statistics"].get("viewCount", 0)),
                "like_count": int(video["statistics"].get("likeCount", 0)),
                "comment_count": int(video["statistics"].get("commentCount", 0)),
                "duration": video["contentDetails"]["duration"],
                "thumbnail": video["snippet"]["thumbnails"]["high"]["url"],
            }
            videos_data.append(video_data)
        
        # Sort by view count (highest first)
        videos_data.sort(key=lambda x: x["view_count"], reverse=True)
        
        return videos_data
    
    except Exception as e:
        logger.error(f"Error searching YouTube videos: {e}")
        return []


def download_youtube_video(video_id: str, output_dir: str = config.DEFAULT_TEMP_DIR) -> str:
    """
    Download a YouTube video by its ID.
    
    Args:
        video_id: YouTube video ID
        output_dir: Directory to save the video
        
    Returns:
        Path to the downloaded video file
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        # Create YouTube object
        yt = YouTube(f"https://www.youtube.com/watch?v={video_id}")
        
        # Get the highest resolution stream
        stream = yt.streams.get_highest_resolution()
        
        # Download the video
        output_path = stream.download(output_path=output_dir)
        
        logger.info(f"Downloaded video: {yt.title}")
        return output_path
    
    except Exception as e:
        logger.error(f"Error downloading video {video_id}: {e}")
        raise


def analyze_video_engagement(
    video_path: str,
) -> List[Dict[str, Any]]:
    """
    Analyze video to identify segments with high engagement potential.
    This is a simple implementation that divides the video into segments.
    In a real application, this would use more sophisticated algorithms.
    
    Args:
        video_path: Path to the video file
        
    Returns:
        List of high engagement segments with start and end times
    """
    if not CV2_AVAILABLE:
        # Fallback when OpenCV is not available
        segments = []
        
        # Generate random segments (each 30 seconds long)
        for i in range(5):  # Generate 5 segments
            start_time = i * 30
            end_time = start_time + 30
            
            segments.append({
                "start_time": start_time,
                "end_time": end_time,
                "engagement_score": random.uniform(0.7, 1.0),
                "caption": f"Interesting moment {i+1}"
            })
        
        # Sort segments by engagement score (highest first)
        segments.sort(key=lambda x: x["engagement_score"], reverse=True)
        
        return segments
    
    try:
        # Open the video file
        video = cv2.VideoCapture(video_path)
        
        # Get video properties
        fps = video.get(cv2.CAP_PROP_FPS)
        frame_count = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps
        
        # For this simple implementation, we'll divide the video into equal segments
        # and randomly assign engagement scores
        num_segments = max(int(duration / 10), 5)  # Create at least 5 segments
        segment_duration = duration / num_segments
        
        segments = []
        for i in range(num_segments):
            start_time = i * segment_duration
            end_time = (i + 1) * segment_duration
            
            # In a real implementation, this would analyze audio levels, scene changes, etc.
            # Here we're just using random scores
            engagement_score = random.uniform(0.7, 1.0)
            
            segments.append({
                "start_time": start_time,
                "end_time": end_time,
                "engagement_score": engagement_score,
                "caption": f"Interesting moment {i+1}"
            })
        
        # Sort segments by engagement score (highest first)
        segments.sort(key=lambda x: x["engagement_score"], reverse=True)
        
        video.release()
        return segments
    
    except Exception as e:
        logger.error(f"Error analyzing video engagement: {e}")
        # Provide a fallback when analysis fails
        return [
            {
                "start_time": 0,
                "end_time": 30,
                "engagement_score": 0.9,
                "caption": "Check out this highlight!"
            },
            {
                "start_time": 60,
                "end_time": 90,
                "engagement_score": 0.8,
                "caption": "Another great moment!"
            },
            {
                "start_time": 120,
                "end_time": 150,
                "engagement_score": 0.7,
                "caption": "Don't miss this part!"
            }
        ]


def clip_video(
    video_path: str,
    output_path: str,
    start_time: float,
    end_time: float,
    add_captions: bool = True,
    caption_text: str = None,
) -> str:
    """
    Clip a segment from a video and add captions if specified.
    
    Args:
        video_path: Path to the input video
        output_path: Path to save the output clip
        start_time: Start time of the clip in seconds
        end_time: End time of the clip in seconds
        add_captions: Whether to add captions
        caption_text: Text for the caption
        
    Returns:
        Path to the output clip
    """
    if not MOVIEPY_AVAILABLE:
        logger.error("MoviePy is not available. Cannot clip video.")
        return video_path
    
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    try:
        # Load the video
        video = VideoFileClip(video_path).subclip(start_time, end_time)
        
        # Resize to vertical format if needed
        target_width, target_height = config.DEFAULT_RESOLUTION
        
        # If the video is not in the target aspect ratio, resize and add padding
        if video.w / video.h != target_width / target_height:
            # Resize to fit the target height
            scale_factor = target_height / video.h
            resized_width = int(video.w * scale_factor)
            
            # Resize the video
            video = video.resize(height=target_height, width=resized_width)
            
            # If the resized width is less than target width, add padding
            if resized_width < target_width:
                # Create a black background
                bg_clip = VideoFileClip(video_path).subclip(start_time, end_time)
                bg_clip = bg_clip.resize(height=target_height)
                bg_clip = bg_clip.crop(x1=0, x2=target_width, y1=0, y2=target_height)
                
                # Overlay the resized video on the background
                x_offset = (target_width - resized_width) // 2
                video = CompositeVideoClip(
                    [bg_clip, video.set_position((x_offset, 0))], 
                    size=(target_width, target_height)
                )
            # If the resized width is greater than target width, crop it
            elif resized_width > target_width:
                # Crop from the center
                x_offset = (resized_width - target_width) // 2
                video = video.crop(
                    x1=x_offset, 
                    x2=x_offset + target_width, 
                    y1=0, 
                    y2=target_height
                )
        
        # Add captions if specified
        if add_captions and caption_text:
            try:
                # Create text clip
                caption_style = config.DEFAULT_CAPTION_STYLE
                text_clip = TextClip(
                    caption_text,
                    fontsize=caption_style["font_size"],
                    font=caption_style["font"],
                    color=caption_style["color"],
                    stroke_color=caption_style["stroke_color"],
                    stroke_width=caption_style["stroke_width"],
                    method="caption",
                    size=(target_width * 0.9, None),
                )
                
                # Set position
                if caption_style["position"] == "bottom":
                    text_position = ("center", "bottom")
                else:
                    text_position = ("center", "top")
                
                text_clip = text_clip.set_position(text_position).set_duration(video.duration)
                
                # Composite video with text
                video = CompositeVideoClip([video, text_clip])
            except Exception as e:
                logger.error(f"Error adding captions: {e}")
        
        # Write the output file
        video.write_videofile(output_path, codec="libx264", audio_codec="aac")
        
        logger.info(f"Created clip: {output_path}")
        return output_path
    
    except Exception as e:
        logger.error(f"Error clipping video: {e}")
        return video_path


def generate_video_title(video_title: str, segment_index: int) -> str:
    """Generate a title for a clip based on the original video title."""
    return f"{video_title.split('|')[0].strip()} - Highlight {segment_index + 1}"


def extract_captions(video_id: str) -> Dict[float, str]:
    """
    Extract captions from a YouTube video.
    In a real implementation, this would use the YouTube API to get captions.
    Here we're just returning placeholder captions.
    
    Args:
        video_id: YouTube video ID
        
    Returns:
        Dictionary mapping timestamps to caption text
    """
    # Placeholder implementation
    return {
        0: "This is amazing!",
        10: "Check out this awesome content!",
        20: "Don't forget to like and subscribe!",
    } 