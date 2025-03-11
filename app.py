#!/usr/bin/env python3
"""
Streamlit web interface for the YouTube Shorts Auto-Clipper Bot.
"""

import os
import sys
import json
import tempfile
import logging
from typing import List, Dict, Any
import streamlit as st
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Import local modules
import config
import utils
from main import process_videos, setup_openai_client

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="YouTube Shorts Auto-Clipper Bot",
    page_icon="✂️",
    layout="wide",
)


def check_api_keys():
    """Check if required API keys are set."""
    youtube_api_key = os.getenv("YOUTUBE_API_KEY")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    
    if not youtube_api_key:
        st.warning(
            "⚠️ YouTube API key not found. Please enter it below to enable video search functionality."
        )
    
    if not openai_api_key:
        st.warning(
            "⚠️ OpenAI API key not found. The app will use a fallback method for video analysis."
        )


def show_homepage():
    """Show the homepage with app description and features."""
    st.title("YouTube Shorts Auto-Clipper Bot")
    st.subheader("Create engaging short-form content from viral videos")
    
    # App description
    st.markdown(
        """
        This AI-powered tool helps content creators automate the process of:
        
        1. **Finding trending content** across YouTube
        2. **Analyzing videos** to identify the most engaging moments
        3. **Creating short-form clips** optimized for platforms like YouTube Shorts, TikTok, and Instagram Reels
        
        The app uses AI to make intelligent decisions about what content to clip and how to present it for maximum engagement.
        """
    )
    
    # Feature cards
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(
            """
            ### 🔍 Smart Content Discovery
            * Finds trending and viral videos
            * Focuses on your chosen topics
            * Identifies high-engagement content
            """
        )
    
    with col2:
        st.markdown(
            """
            ### 🧠 AI-Powered Analysis
            * Identifies the most engaging moments
            * Creates compelling captions
            * Optimizes for viewer retention
            """
        )
    
    with col3:
        st.markdown(
            """
            ### ✂️ Automated Editing
            * Clips videos to optimal length
            * Formats for different platforms
            * Adds captions and effects
            """
        )
    
    # Call to action
    st.markdown("---")
    st.subheader("Ready to create viral short-form content?")
    if st.button("Get Started", type="primary", use_container_width=True):
        st.session_state.page = "create"


def show_api_settings():
    """Show API settings page."""
    st.title("API Settings")
    
    # YouTube API key
    youtube_api_key = os.getenv("YOUTUBE_API_KEY", "")
    new_youtube_api_key = st.text_input(
        "YouTube API Key",
        value=youtube_api_key,
        type="password",
        help="Required for searching and downloading YouTube videos",
    )
    
    # OpenAI API key
    openai_api_key = os.getenv("OPENAI_API_KEY", "")
    new_openai_api_key = st.text_input(
        "OpenAI API Key",
        value=openai_api_key,
        type="password",
        help="Optional, but enables AI-powered content analysis and recommendations",
    )
    
    # Save API keys
    if st.button("Save API Keys", type="primary"):
        # Update environment variables
        os.environ["YOUTUBE_API_KEY"] = new_youtube_api_key
        os.environ["OPENAI_API_KEY"] = new_openai_api_key
        
        # Save to .env file
        with open(".env", "w") as f:
            f.write(f"YOUTUBE_API_KEY={new_youtube_api_key}\n")
            f.write(f"OPENAI_API_KEY={new_openai_api_key}\n")
        
        st.success("API keys saved successfully!")
        st.rerun()


def show_create_page():
    """Show the create page for generating clips."""
    st.title("Create Short-Form Content")
    
    # Check API keys
    check_api_keys()
    
    # Create form
    with st.form("create_form"):
        # Topic input
        topic = st.text_input(
            "Topic or Search Query",
            value="trending gaming",
            help="Enter a topic, keyword, or search query to find videos",
        )
        
        # Number of clips
        num_clips = st.slider(
            "Number of Clips to Generate",
            min_value=1,
            max_value=10,
            value=3,
            help="How many short-form clips to create",
        )
        
        # Clip duration
        clip_duration = st.slider(
            "Clip Duration (seconds)",
            min_value=10,
            max_value=60,
            value=30,
            help="Duration of each clip in seconds",
        )
        
        # Output format
        output_format = st.selectbox(
            "Output Format",
            options=["youtube_shorts", "tiktok", "instagram_reels"],
            format_func=lambda x: x.replace("_", " ").title(),
            help="Format the clips for your target platform",
        )
        
        # Advanced options
        with st.expander("Advanced Options"):
            keep_temp = st.checkbox(
                "Keep Temporary Files",
                value=False,
                help="Keep downloaded videos and temporary files after processing",
            )
        
        # Submit button
        submitted = st.form_submit_button("Create Clips", type="primary", use_container_width=True)
    
    # Process form submission
    if submitted:
        # Check YouTube API key
        if not os.getenv("YOUTUBE_API_KEY"):
            st.error("YouTube API key is required. Please set it in the API Settings page.")
            return
        
        # Set up progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Create a temporary directory for output
        with tempfile.TemporaryDirectory() as temp_output_dir:
            # Update status
            status_text.text("Searching for videos...")
            progress_bar.progress(10)
            
            try:
                # Process videos
                clips_info = []
                
                # Create container for real-time updates
                update_container = st.container()
                
                # Override standard output to capture logs
                class StreamlitLogger:
                    def __init__(self, container):
                        self.container = container
                        self.log_text = ""
                    
                    def write(self, text):
                        self.log_text += text
                        self.container.code(self.log_text)
                        return len(text)
                    
                    def flush(self):
                        pass
                
                logger_container = st.container()
                streamlit_logger = StreamlitLogger(logger_container)
                sys.stdout = streamlit_logger
                
                # Process videos
                process_videos(
                    topic=topic,
                    output_dir=temp_output_dir,
                    num_clips=num_clips,
                    clip_duration=clip_duration,
                    output_format=output_format,
                    keep_temp=keep_temp,
                )
                
                # Restore standard output
                sys.stdout = sys.__stdout__
                
                # Get list of generated clips
                clips = [f for f in os.listdir(temp_output_dir) if f.endswith(".mp4")]
                
                if not clips:
                    st.error("No clips were generated. Please try a different topic or check logs for errors.")
                    return
                
                # Update status
                status_text.text("Clips generated successfully!")
                progress_bar.progress(100)
                
                # Display the generated clips
                st.subheader("Generated Clips")
                
                for i, clip_file in enumerate(clips):
                    clip_path = os.path.join(temp_output_dir, clip_file)
                    
                    # Look for metadata file
                    metadata_file = clip_file.replace(".mp4", "_metadata.json")
                    metadata_path = os.path.join(temp_output_dir, metadata_file)
                    
                    clip_metadata = None
                    if os.path.exists(metadata_path):
                        with open(metadata_path, "r") as f:
                            clip_metadata = json.load(f)
                    
                    # Display clip and info
                    col1, col2 = st.columns([2, 3])
                    
                    with col1:
                        st.video(clip_path)
                    
                    with col2:
                        if clip_metadata:
                            st.subheader(clip_metadata.get("title", f"Clip {i+1}"))
                            st.markdown(clip_metadata.get("description", ""))
                            
                            st.markdown("#### Suggested Tags")
                            tags = clip_metadata.get("tags", [])
                            if tags:
                                st.markdown(" ".join([f"`{tag}`" for tag in tags]))
                            
                            if "thumbnail_description" in clip_metadata:
                                st.markdown("#### Thumbnail Idea")
                                st.markdown(clip_metadata.get("thumbnail_description", ""))
                        else:
                            st.subheader(f"Clip {i+1}")
                            st.markdown(f"Generated from topic: {topic}")
                    
                    # Download button for the clip
                    with open(clip_path, "rb") as f:
                        st.download_button(
                            label=f"Download Clip {i+1}",
                            data=f,
                            file_name=clip_file,
                            mime="video/mp4",
                        )
                    
                    st.markdown("---")
            
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
                logger.exception("Error in clip generation")


def show_about_page():
    """Show the About page."""
    st.title("About YouTube Shorts Auto-Clipper Bot")
    
    st.markdown(
        """
        ## How It Works
        
        This application uses a combination of AI technologies to automate the process of creating short-form content:
        
        1. **Content Discovery**: The app searches YouTube for trending or viral videos based on your chosen topic.
        
        2. **Content Analysis**: Using OpenAI GPT models, the app analyzes videos to identify the most engaging segments.
        
        3. **Video Processing**: The app clips the best moments and enhances them with captions and effects.
        
        4. **Output Generation**: The final result is a set of short-form videos optimized for platforms like YouTube Shorts, TikTok, and Instagram Reels.
        
        ## Technologies Used
        
        - **Python**: The core programming language
        - **OpenAI**: Provides language models for content analysis
        - **YouTube API**: Used for searching and downloading videos
        - **FFmpeg & MoviePy**: Used for video processing
        - **Streamlit**: Powers this web interface
        
        ## License
        
        This project is released under the MIT License.
        
        ## Creator
        
        Made with ❤️ for content creators everywhere.
        """
    )


def main():
    """Main function for the Streamlit app."""
    # Initialize session state
    if "page" not in st.session_state:
        st.session_state.page = "home"
    
    # Sidebar navigation
    with st.sidebar:
        st.title("Navigation")
        
        if st.button("Home", use_container_width=True):
            st.session_state.page = "home"
        
        if st.button("Create Content", use_container_width=True):
            st.session_state.page = "create"
        
        if st.button("API Settings", use_container_width=True):
            st.session_state.page = "settings"
        
        if st.button("About", use_container_width=True):
            st.session_state.page = "about"
        
        st.markdown("---")
        st.markdown("Made with ❤️ by AI")
    
    # Display the selected page
    if st.session_state.page == "home":
        show_homepage()
    elif st.session_state.page == "create":
        show_create_page()
    elif st.session_state.page == "settings":
        show_api_settings()
    elif st.session_state.page == "about":
        show_about_page()


if __name__ == "__main__":
    main() 