"""
Configuration settings for the YouTube Shorts Auto-Clipper Bot.
"""

# YouTube API settings
YOUTUBE_MAX_RESULTS = 10
YOUTUBE_SEARCH_CRITERIA = {
    "trending": "view_count",
    "recent": "date",
    "relevance": "relevance",
    "rating": "rating",
}
DEFAULT_SEARCH_ORDER = "trending"

# Video processing settings
DEFAULT_CLIP_DURATION = 30  # seconds
DEFAULT_NUM_CLIPS = 3
DEFAULT_OUTPUT_FORMAT = "mp4"
DEFAULT_RESOLUTION = (1080, 1920)  # vertical video (9:16 ratio)
DEFAULT_OUTPUT_DIR = "./output"
DEFAULT_TEMP_DIR = "./temp"

# Content types
CONTENT_TYPES = {
    "youtube_shorts": {
        "max_duration": 60,
        "resolution": (1080, 1920),
        "aspect_ratio": "9:16",
    },
    "tiktok": {
        "max_duration": 60,
        "resolution": (1080, 1920),
        "aspect_ratio": "9:16",
    },
    "instagram_reels": {
        "max_duration": 90,
        "resolution": (1080, 1920),
        "aspect_ratio": "9:16",
    },
}

# CrewAI agent configuration
AGENT_CONFIG = {
    "researcher": {
        "role": "Content Researcher",
        "goal": "Find trending and viral videos based on user preferences",
        "backstory": """You are an expert content researcher who understands
                      trends and viral content. You know how to identify videos
                      that have potential for creating engaging short-form content.""",
    },
    "content_analyzer": {
        "role": "Content Analyzer",
        "goal": "Analyze videos to identify the most engaging segments",
        "backstory": """You are a content analysis expert who can identify the most
                      captivating moments in a video. You understand human psychology
                      and what makes content go viral.""",
    },
    "video_editor": {
        "role": "Video Editor",
        "goal": "Edit and enhance video clips to maximize engagement",
        "backstory": """You are a professional video editor with years of experience
                      in creating short-form content. You know how to transform raw
                      footage into compelling videos that capture viewers' attention.""",
    },
}

# Styling options
DEFAULT_CAPTION_STYLE = {
    "font": "Arial",
    "font_size": 30,
    "color": "white",
    "stroke_color": "black",
    "stroke_width": 2,
    "position": "bottom",
}

DEFAULT_EFFECTS = [
    "auto_caption",
    "zoom_points_of_interest",
    "background_music",
] 