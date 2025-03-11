#!/usr/bin/env python3
"""
Main script for the YouTube Shorts Auto-Clipper Bot.
"""

import os
import argparse
import json
import logging
from typing import List, Dict, Any
import random
from dotenv import load_dotenv
import openai

import config
import utils

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="YouTube Shorts Auto-Clipper Bot"
    )
    parser.add_argument(
        "--topic",
        type=str,
        default="trending",
        help="Topic or search query for finding videos",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default=config.DEFAULT_OUTPUT_DIR,
        help="Directory to save output clips",
    )
    parser.add_argument(
        "--clips",
        type=int,
        default=config.DEFAULT_NUM_CLIPS,
        help="Number of clips to generate",
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=config.DEFAULT_CLIP_DURATION,
        help="Duration of each clip in seconds",
    )
    parser.add_argument(
        "--api_key",
        type=str,
        help="YouTube API key (overrides environment variable)",
    )
    parser.add_argument(
        "--output_format",
        type=str,
        default="youtube_shorts",
        choices=["youtube_shorts", "tiktok", "instagram_reels"],
        help="Output format for the clips",
    )
    parser.add_argument(
        "--keep_temp",
        action="store_true",
        help="Keep temporary files after processing",
    )
    
    return parser.parse_args()


def setup_openai_client():
    """
    Set up the OpenAI client for AI analysis.
    
    Returns:
        OpenAI client if API key is available, None otherwise
    """
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if openai_api_key:
        logger.info("Using OpenAI for content analysis")
        openai.api_key = openai_api_key
        return openai
    else:
        logger.info("No OpenAI API key found, using fallback analysis method")
        return None


def analyze_video_with_ai(client, video_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Use OpenAI to analyze a video and suggest engaging segments.
    
    Args:
        client: OpenAI client
        video_data: Dictionary with video information
        
    Returns:
        List of suggested segments with start/end times and captions
    """
    if not client:
        return []
    
    try:
        # Create prompt for analysis
        prompt = f"""
        Analyze this YouTube video to find the most engaging moments for short-form content:
        
        Title: {video_data['title']}
        Channel: {video_data['channel']}
        Description: {video_data['description']}
        
        Identify 3-5 segments that would make great short-form clips (30-60 seconds each).
        For each segment, specify:
        1. Start time (in seconds)
        2. End time (in seconds)
        3. A brief, engaging caption for the clip
        
        Format your response as a JSON array of objects with the keys: start_time, end_time, engagement_score, and caption.
        Estimate the engagement_score from 0.0 to 1.0 based on how engaging you think the segment would be.
        """
        
        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "You are a content analysis expert who can identify the most engaging segments of videos."},
                {"role": "user", "content": prompt}
            ]
        )
        
        # Parse and validate response
        result = json.loads(response.choices[0].message.content)
        segments = result.get("segments", [])
        
        if not segments and "segments" not in result:
            # Try to parse the entire response as a list
            segments = result if isinstance(result, list) else []
        
        # Ensure segments have required fields
        validated_segments = []
        for segment in segments:
            if "start_time" in segment and "end_time" in segment:
                segment["engagement_score"] = segment.get("engagement_score", random.uniform(0.7, 1.0))
                segment["caption"] = segment.get("caption", "Check out this highlight!")
                validated_segments.append(segment)
        
        return validated_segments
    
    except Exception as e:
        logger.error(f"Error analyzing video with AI: {e}")
        return []


def generate_video_metadata(client, video_data: Dict[str, Any], clip_data: Dict[str, Any], output_format: str) -> Dict[str, Any]:
    """
    Generate metadata for a video clip using AI.
    
    Args:
        client: OpenAI client
        video_data: Dictionary with video information
        clip_data: Dictionary with clip information
        output_format: The format of the output clip
        
    Returns:
        Dictionary with metadata for the clip
    """
    if not client:
        return {
            "title": f"{video_data['title']} - Highlight",
            "description": f"Check out this highlight from {video_data['channel']}!",
            "tags": [output_format, "highlight", "trending", "viral"],
            "thumbnail_description": "Thumbnail showing the most exciting moment from the clip.",
        }
    
    try:
        # Create prompt for metadata generation
        prompt = f"""
        Generate metadata for a short-form video clip:
        
        Original Video:
        Title: {video_data['title']}
        Channel: {video_data['channel']}
        Description: {video_data['description']}
        
        Clip Information:
        Caption: {clip_data['caption']}
        Duration: {clip_data['end_time'] - clip_data['start_time']} seconds
        Platform: {output_format.replace('_', ' ').title()}
        
        Generate the following:
        1. An attention-grabbing title (max 60 characters)
        2. A compelling description (max 300 characters)
        3. Up to 10 relevant tags as an array of strings
        4. A description of what would make a good thumbnail for this clip
        
        Format your response as a JSON object with keys: title, description, tags, thumbnail_description
        """
        
        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "You are a social media marketing expert who creates engaging metadata for short-form videos."},
                {"role": "user", "content": prompt}
            ]
        )
        
        # Parse response
        result = json.loads(response.choices[0].message.content)
        
        return result
    
    except Exception as e:
        logger.error(f"Error generating metadata with AI: {e}")
        return {
            "title": f"{video_data['title']} - Highlight",
            "description": f"Check out this highlight from {video_data['channel']}!",
            "tags": [output_format, "highlight", "trending", "viral"],
            "thumbnail_description": "Thumbnail showing the most exciting moment from the clip.",
        }


def process_videos(
    topic: str,
    output_dir: str,
    num_clips: int,
    clip_duration: int,
    output_format: str,
    keep_temp: bool = False,
):
    """
    Process videos to create short-form clips.
    
    Args:
        topic: Topic or search query for finding videos
        output_dir: Directory to save output clips
        num_clips: Number of clips to generate
        clip_duration: Duration of each clip in seconds
        output_format: Output format for the clips
        keep_temp: Whether to keep temporary files after processing
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Create temp directory if it doesn't exist
    temp_dir = config.DEFAULT_TEMP_DIR
    os.makedirs(temp_dir, exist_ok=True)
    
    # Set up OpenAI client
    openai_client = setup_openai_client()
    
    try:
        logger.info(f"Searching for videos on topic: {topic}")
        
        # Search for videos
        videos_data = utils.search_youtube_videos(topic)
        
        # Limit to the top videos
        videos_data = videos_data[:config.YOUTUBE_MAX_RESULTS]
        
        if not videos_data:
            logger.error("No videos found matching the search query")
            return
        
        # Process each video
        clips_created = 0
        for video_data in videos_data:
            if clips_created >= num_clips:
                break
            
            try:
                # Download the video
                video_id = video_data["id"]
                logger.info(f"Processing video: {video_data['title']} (ID: {video_id})")
                
                video_path = utils.download_youtube_video(video_id, temp_dir)
                
                # Analyze video for engaging segments
                segments = analyze_video_with_ai(openai_client, video_data)
                
                # If AI analysis failed, use fallback method
                if not segments:
                    logger.info("Using fallback method for content analysis")
                    segments = utils.analyze_video_engagement(video_path)
                
                # Process segments to create clips
                for i, segment in enumerate(segments):
                    if clips_created >= num_clips:
                        break
                    
                    try:
                        # Ensure segment duration matches requested clip duration
                        start_time = segment["start_time"]
                        end_time = min(start_time + clip_duration, segment.get("end_time", start_time + clip_duration))
                        
                        # Get caption for the segment
                        caption = segment.get("caption", f"Check out this {topic} content!")
                        
                        # Generate output path
                        clip_filename = f"{video_id}_clip_{i + 1}.mp4"
                        clip_path = os.path.join(output_dir, clip_filename)
                        
                        # Create the clip
                        utils.clip_video(
                            video_path=video_path,
                            output_path=clip_path,
                            start_time=start_time,
                            end_time=end_time,
                            add_captions=True,
                            caption_text=caption,
                        )
                        
                        # Generate metadata for the clip
                        metadata = generate_video_metadata(
                            openai_client, 
                            video_data, 
                            segment, 
                            output_format
                        )
                        
                        # Save metadata
                        metadata_path = os.path.join(output_dir, f"{video_id}_clip_{i + 1}_metadata.json")
                        with open(metadata_path, "w") as f:
                            json.dump(metadata, f, indent=2)
                        
                        clips_created += 1
                        logger.info(f"Created clip {clips_created}/{num_clips}: {clip_path}")
                    
                    except Exception as e:
                        logger.error(f"Error creating clip: {e}")
            
            except Exception as e:
                logger.error(f"Error processing video {video_data.get('id', 'unknown')}: {e}")
        
        # Clean up temporary files
        if not keep_temp:
            for file in os.listdir(temp_dir):
                file_path = os.path.join(temp_dir, file)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                except Exception as e:
                    logger.error(f"Error deleting temporary file {file_path}: {e}")
        
        logger.info(f"Processing complete. Created {clips_created} clips in {output_dir}")
    
    except Exception as e:
        logger.error(f"Error in video processing: {e}")


def main():
    """Main function."""
    # Parse command line arguments
    args = parse_args()
    
    # Set YouTube API key from arguments if provided
    if args.api_key:
        os.environ["YOUTUBE_API_KEY"] = args.api_key
    
    # Process videos
    process_videos(
        topic=args.topic,
        output_dir=args.output_dir,
        num_clips=args.clips,
        clip_duration=args.duration,
        output_format=args.output_format,
        keep_temp=args.keep_temp,
    )


if __name__ == "__main__":
    main() 