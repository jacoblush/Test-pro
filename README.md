# YouTube Shorts Auto-Clipper Bot

An AI-powered application that automatically finds viral videos, analyzes content, and creates short-form videos for platforms like YouTube Shorts, TikTok, and Instagram Reels.

## Features

- 🔍 **Smart Content Discovery**: Automatically finds trending and viral videos
- 🧠 **AI-Powered Analysis**: Uses CrewAI to identify the most engaging parts of videos
- ✂️ **Automated Clipping**: Extracts the best moments to create compelling short-form content
- 🎨 **Content Enhancement**: Adds captions, effects, and transitions
- 📱 **Multi-Platform Support**: Creates content optimized for YouTube Shorts, TikTok, and Instagram

## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/youtube-shorts-clipper.git
cd youtube-shorts-clipper
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the root directory with your API keys:
```
YOUTUBE_API_KEY=your_youtube_api_key
OPENAI_API_KEY=your_openai_api_key
```

## Usage

### Start the Web Interface

```bash
streamlit run app.py
```

### Using the Command Line

```bash
python main.py --topic "trending gaming" --output_dir "./output" --clips 3
```

### Parameters

- `--topic`: The topic or search query to find videos (default: "trending")
- `--output_dir`: Directory to save output clips (default: "./output")
- `--clips`: Number of clips to generate (default: 3)
- `--duration`: Duration of each clip in seconds (default: 30)

## How It Works

1. **Content Discovery**: Searches YouTube for trending or viral videos in your chosen niche
2. **Content Analysis**: Uses AI to identify the most engaging parts of the videos
3. **Video Processing**: Clips the best moments and enhances them with captions and effects
4. **Output Generation**: Creates short-form videos ready for publishing

## Customization

Edit the `config.py` file to customize:
- Video search parameters
- Clip duration and effects
- Output format and quality

## License

MIT License 