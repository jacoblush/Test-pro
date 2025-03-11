"""
CrewAI agents for the YouTube Shorts Auto-Clipper Bot.
"""

import os
from typing import List, Dict, Any
from pydantic import BaseModel
from crewai import Agent, Task, Crew
from crewai_tools import SerperDevTool, WebScraperTool
import config

class VideoData(BaseModel):
    """Data model for video information."""
    id: str
    title: str
    channel: str
    view_count: int
    like_count: int
    description: str


class ClipData(BaseModel):
    """Data model for clip information."""
    start_time: float
    end_time: float
    engagement_score: float
    caption: str = ""


class ContentResearcherAgent:
    """Agent responsible for finding trending and viral videos."""
    
    def __init__(self, llm=None):
        """Initialize the ContentResearcherAgent."""
        self.agent_config = config.AGENT_CONFIG["researcher"]
        
        # Tools for the agent
        self.tools = [
            SerperDevTool(),
            WebScraperTool(),
        ]
        
        # Create the agent
        self.agent = Agent(
            role=self.agent_config["role"],
            goal=self.agent_config["goal"],
            backstory=self.agent_config["backstory"],
            tools=self.tools,
            llm=llm,
            verbose=True,
        )
    
    def get_agent(self):
        """Return the CrewAI agent."""
        return self.agent
    
    def create_research_task(self, topic: str) -> Task:
        """
        Create a task for researching trending videos on a given topic.
        
        Args:
            topic: The topic to research
            
        Returns:
            A CrewAI Task object
        """
        return Task(
            description=f"""
            Research trending videos about "{topic}" on YouTube.
            Identify videos that have viral potential or are already trending.
            Focus on videos with engaging content, high view counts, and positive engagement.
            Return a list of at least 5 video IDs with their titles, channel names, and view counts.
            Format your response as a list of JSON objects.
            """,
            expected_output="""
            [
                {
                    "id": "video_id_1",
                    "title": "Video Title 1",
                    "channel": "Channel Name 1",
                    "view_count": 1000000,
                    "like_count": 50000,
                    "description": "Brief description of the video"
                },
                ...
            ]
            """,
            agent=self.agent,
        )


class ContentAnalyzerAgent:
    """Agent responsible for analyzing videos to identify engaging segments."""
    
    def __init__(self, llm=None):
        """Initialize the ContentAnalyzerAgent."""
        self.agent_config = config.AGENT_CONFIG["content_analyzer"]
        
        # Create the agent
        self.agent = Agent(
            role=self.agent_config["role"],
            goal=self.agent_config["goal"],
            backstory=self.agent_config["backstory"],
            llm=llm,
            verbose=True,
        )
    
    def get_agent(self):
        """Return the CrewAI agent."""
        return self.agent
    
    def create_analysis_task(self, video_data: Dict[str, Any]) -> Task:
        """
        Create a task for analyzing a video to identify engaging segments.
        
        Args:
            video_data: Dictionary with video information
            
        Returns:
            A CrewAI Task object
        """
        return Task(
            description=f"""
            Analyze the video titled "{video_data['title']}" from channel "{video_data['channel']}".
            Description: {video_data['description']}
            
            Based on the title and description, identify potential engaging moments in the video.
            Consider what parts of the video would be most captivating for short-form content.
            
            Return a list of at least 3 time segments (start and end times) that you believe would make good clips.
            For each segment, provide a caption that would be engaging for viewers.
            Format your response as a list of JSON objects.
            """,
            expected_output="""
            [
                {
                    "start_time": 120,
                    "end_time": 150,
                    "engagement_score": 0.9,
                    "caption": "This amazing moment will blow your mind!"
                },
                ...
            ]
            """,
            agent=self.agent,
        )


class VideoEditorAgent:
    """Agent responsible for editing and enhancing video clips."""
    
    def __init__(self, llm=None):
        """Initialize the VideoEditorAgent."""
        self.agent_config = config.AGENT_CONFIG["video_editor"]
        
        # Create the agent
        self.agent = Agent(
            role=self.agent_config["role"],
            goal=self.agent_config["goal"],
            backstory=self.agent_config["backstory"],
            llm=llm,
            verbose=True,
        )
    
    def get_agent(self):
        """Return the CrewAI agent."""
        return self.agent
    
    def create_editing_task(
        self, 
        video_data: Dict[str, Any], 
        clip_data: Dict[str, Any],
        output_format: str = "youtube_shorts",
    ) -> Task:
        """
        Create a task for editing a video clip.
        
        Args:
            video_data: Dictionary with video information
            clip_data: Dictionary with clip information
            output_format: The format of the output clip (youtube_shorts, tiktok, instagram_reels)
            
        Returns:
            A CrewAI Task object
        """
        format_specs = config.CONTENT_TYPES.get(output_format, config.CONTENT_TYPES["youtube_shorts"])
        
        return Task(
            description=f"""
            Edit the clip from video "{video_data['title']}" by "{video_data['channel']}".
            The clip starts at {clip_data['start_time']} seconds and ends at {clip_data['end_time']} seconds.
            
            Create an engaging {output_format} video with the following specifications:
            - Maximum duration: {format_specs['max_duration']} seconds
            - Resolution: {format_specs['resolution']}
            - Aspect ratio: {format_specs['aspect_ratio']}
            
            Add the following caption to the video: "{clip_data['caption']}"
            
            Consider adding the following enhancements:
            - Zoom effects at key moments
            - Text overlays for emphasis
            - Background music
            - Transitions between scenes (if applicable)
            
            Return a description of the editing choices you've made and why.
            """,
            expected_output="""
            {
                "title": "Engaging title for the clip",
                "description": "Description of the clip for posting",
                "editing_choices": "Description of the editing choices made",
                "tags": ["tag1", "tag2", "tag3"],
                "thumbnail_description": "Description of what would make a good thumbnail"
            }
            """,
            agent=self.agent,
        )


def create_video_processing_crew(llm=None):
    """
    Create a CrewAI crew for video processing.
    
    Args:
        llm: Language model to use for the agents
        
    Returns:
        A CrewAI Crew object
    """
    # Create agents
    researcher_agent = ContentResearcherAgent(llm=llm)
    analyzer_agent = ContentAnalyzerAgent(llm=llm)
    editor_agent = VideoEditorAgent(llm=llm)
    
    # Create crew
    crew = Crew(
        agents=[
            researcher_agent.get_agent(),
            analyzer_agent.get_agent(),
            editor_agent.get_agent(),
        ],
        tasks=[],  # Tasks will be added dynamically
        verbose=True,
    )
    
    return crew, researcher_agent, analyzer_agent, editor_agent 