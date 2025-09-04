"""Market research tools for content analysis."""

import logging
import subprocess
import json
import os
import requests
from typing import List, Dict, Optional
from dotenv import load_dotenv

try:
    import yt_dlp
    YT_DLP_AVAILABLE = True
except ImportError:
    YT_DLP_AVAILABLE = False

load_dotenv()
logger = logging.getLogger(__name__)


def search_youtube_videos(search_term: str, max_results: int = 10) -> List[Dict[str, str]]:
    """
    Search YouTube for videos matching the given term using yt-dlp.
    
    First tries command-line yt-dlp, then falls back to Python module.
    Returns top N video titles with description, view count, and duration.
    """
    # Try command-line yt-dlp first
    try:
        cmd = [
            'yt-dlp',
            '--dump-json',
            '--no-download',
            '--flat-playlist',
            '--ignore-errors',
            '--no-warnings',
            '--user-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            f'ytsearch{max_results}:{search_term}'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        videos = []
        for line in result.stdout.strip().split('\n'):
            if line:
                try:
                    data = json.loads(line)
                    # Handle flat playlist data which has limited info
                    description = data.get('description') or data.get('title', 'No description')
                    if description and len(description) > 200:
                        description = description[:200] + '...'
                    
                    video_info = {
                        'title': data.get('title', 'No title'),
                        'description': description,
                        'view_count': str(data.get('view_count', 'Unknown')),
                        'duration': str(data.get('duration', 'Unknown'))
                    }
                    videos.append(video_info)
                except json.JSONDecodeError:
                    continue
        
        return videos
        
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        logger.info(f"Command-line yt-dlp failed, trying Python module: {e}")
        
        # Fallback to Python module
        if not YT_DLP_AVAILABLE:
            logger.error("yt-dlp Python module not available. Install with: pip install yt-dlp")
            return []
        
        try:
            # Use yt-dlp Python module with search-only configuration
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,  # Only extract basic search info, no format details
                'skip_download': True,
                'ignoreerrors': True,
                'no_color': True,
                'headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                search_results = ydl.extract_info(
                    f'ytsearch{max_results}:{search_term}',
                    download=False
                )
                
                videos = []
                if search_results and 'entries' in search_results:
                    for entry in search_results['entries']:
                        if entry:
                            # Use the data from the search results directly
                            # For flat extraction, description might not be available
                            description = entry.get('description') or entry.get('title', 'No description')
                            if description and len(description) > 200:
                                description = description[:200] + '...'
                            
                            video_data = {
                                'title': entry.get('title', 'No title'),
                                'description': description,
                                'view_count': str(entry.get('view_count', 'Unknown')),
                                'duration': str(entry.get('duration', 'Unknown'))
                            }
                            videos.append(video_data)
                
                return videos
                
        except Exception as module_error:
            logger.error(f"yt-dlp Python module failed: {module_error}")
            return []
    
    except Exception as e:
        logger.error(f"Error searching YouTube: {e}")
        return []


def analyze_video_content_with_llm(videos: List[Dict[str, str]]) -> str:
    """
    Analyze video content using DeepSeek to identify common themes vs unique opportunities.
    """
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        logger.error("OPENROUTER_API_KEY not found")
        return "API key not configured"
    
    if not videos:
        return "No videos to analyze"
    
    # Format video data for analysis
    video_summaries = []
    for i, video in enumerate(videos, 1):
        summary = f"{i}. Title: {video['title']}\n   Description: {video['description']}\n   Views: {video['view_count']}, Duration: {video['duration']}\n"
        video_summaries.append(summary)
    
    video_data = "\n".join(video_summaries)
    
    prompt = f"""Analyze these YouTube videos and answer: "What do these videos commonly cover vs what unique angles could be explored based on the available research?"

Video Data:
{video_data}

Please provide:
1. Common themes/topics covered across these videos
2. Unique angles or perspectives that could be explored
3. Content gaps or opportunities for differentiation

Be specific and actionable in your analysis.

Lead with a short list of Actionable Items based on your analyis
"""
    
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "deepseek/deepseek-chat",
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content']
        else:
            logger.error(f"API request failed: {response.status_code}")
            return f"API error: {response.status_code}"
            
    except Exception as e:
        logger.error(f"Error analyzing videos: {e}")
        return f"Analysis failed: {str(e)}"


def extract_title_patterns(videos: List[Dict[str, str]]) -> List[str]:
    """
    Extract common title patterns from video data using LLM analysis.
    """
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        logger.error("OPENROUTER_API_KEY not found")
        return ["API key not configured"]
    
    if not videos:
        return ["No videos to analyze"]
    
    # Extract just titles for pattern analysis
    titles = [video['title'] for video in videos]
    titles_text = "\n".join([f"{i+1}. {title}" for i, title in enumerate(titles)])
    
    prompt = f"""Analyze these YouTube video titles and identify common patterns. Focus on structural patterns, formatting, and phrasing conventions.

Video Titles:
{titles_text}

Please identify and list the most common title patterns you observe. Examples of patterns might be:
- "How to [action]" format
- "[Number] Ways to [achieve something]"
- "[Topic]: [Explanation]" format
- Questions starting with "Why/What/How"
- Clickbait patterns with numbers or superlatives

Return ONLY a simple list of the patterns you identify, one pattern per line, without explanations or extra text."""
    
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "deepseek/deepseek-chat",
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content'].strip()
            # Split into lines and clean up
            patterns = [line.strip() for line in content.split('\n') if line.strip()]
            return patterns
        else:
            logger.error(f"API request failed: {response.status_code}")
            return [f"API error: {response.status_code}"]
            
    except Exception as e:
        logger.error(f"Error extracting title patterns: {e}")
        return [f"Pattern extraction failed: {str(e)}"]


def analyze_video_topics(videos: List[Dict[str, str]]) -> List[str]:
    """
    Analyze what topics are covered based on video descriptions and titles.
    """
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        logger.error("OPENROUTER_API_KEY not found")
        return ["API key not configured"]
    
    if not videos:
        return ["No videos to analyze"]
    
    # Format titles and descriptions for analysis
    video_content = []
    for i, video in enumerate(videos, 1):
        content = f"{i}. Title: {video['title']}\n   Description: {video['description']}\n"
        video_content.append(content)
    
    video_data = "\n".join(video_content)
    
    prompt = f"""Analyze these YouTube videos and identify the main topics/subjects being covered based on their titles and descriptions.

Video Data:
{video_data}

Please identify the key topics, themes, and subject areas covered across these videos. Focus on:
- Main subject areas (e.g., technology, health, education, etc.)
- Specific subtopics within those areas
- Common themes or angles being discussed

Return ONLY a simple list of the topics you identify, one topic per line, without explanations or extra text."""
    
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "deepseek/deepseek-chat",
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content'].strip()
            # Split into lines and clean up
            topics = [line.strip() for line in content.split('\n') if line.strip()]
            return topics
        else:
            logger.error(f"API request failed: {response.status_code}")
            return [f"API error: {response.status_code}"]
            
    except Exception as e:
        logger.error(f"Error analyzing video topics: {e}")
        return [f"Topic analysis failed: {str(e)}"]


def generate_comprehensive_topic_report(topic: str, max_videos: int = 8) -> str:
    """
    Generate a comprehensive markdown report for a given topic combining all analysis functions.
    
    Args:
        topic: The topic to analyze
        max_videos: Maximum number of videos to analyze (default 8)
        
    Returns:
        A formatted markdown report as a string
    """
    from datetime import datetime
    
    # Get current timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Initialize report
    report = f"""# 📊 Market Analysis Report: {topic}

**Generated:** {timestamp}  
**Videos Analyzed:** {max_videos} videos

---

"""
    
    # Step 1: Search for videos
    videos = search_youtube_videos(topic, max_results=max_videos)
    
    if not videos:
        report += """## ❌ Analysis Failed

**Error:** Unable to fetch videos for analysis.

**Possible causes:**
- yt-dlp not installed or configured
- Network connectivity issues  
- YouTube access restrictions

**Recommendation:** Check your yt-dlp installation and try again.
"""
        return report
    
    if isinstance(videos, list) and len(videos) > 0 and "API key not configured" in str(videos[0]):
        report += """## ❌ Analysis Failed

**Error:** API key not configured.

**Solution:** Set your OPENROUTER_API_KEY environment variable.
"""
        return report
    
    # Add video summary section
    report += f"## 📹 Video Dataset Overview\n\n"
    report += f"**Total videos found:** {len(videos)}\n\n"
    
    # Add top videos list
    report += "### Top Videos Analyzed:\n\n"
    for i, video in enumerate(videos[:5], 1):  # Show top 5
        report += f"{i}. **{video['title']}**\n"
        report += f"   - Views: {video['view_count']} | Duration: {video['duration']}\n"
        report += f"   - *{video['description'][:100]}{'...' if len(video['description']) > 100 else ''}*\n\n"
    
    if len(videos) > 5:
        report += f"*...and {len(videos) - 5} more videos*\n\n"
    
    report += "---\n\n"
    
    # Step 2: Title Pattern Analysis
    report += "## 🏷️ Title Pattern Analysis\n\n"
    patterns = extract_title_patterns(videos)
    
    if patterns and not any("error" in str(p).lower() or "failed" in str(p).lower() for p in patterns):
        report += "**Common title patterns identified:**\n\n"
        for i, pattern in enumerate(patterns, 1):
            # Clean up patterns that might have bullet points or dashes
            clean_pattern = pattern.strip('•-* ')
            report += f"{i}. {clean_pattern}\n"
        report += "\n**💡 Insight:** These patterns represent proven engagement formulas in this topic area.\n\n"
    else:
        report += "⚠️ *Pattern analysis unavailable - API key may not be configured*\n\n"
    
    report += "---\n\n"
    
    # Step 3: Topic Coverage Analysis
    report += "## 🎯 Topic Coverage Analysis\n\n"
    topics_covered = analyze_video_topics(videos)
    
    if topics_covered and not any("error" in str(t).lower() or "failed" in str(t).lower() for t in topics_covered):
        report += "**Key topics and themes being covered:**\n\n"
        for i, topic_item in enumerate(topics_covered, 1):
            clean_topic = topic_item.strip('•-* ')
            report += f"- {clean_topic}\n"
        report += "\n**💡 Insight:** This shows the current content landscape and saturation levels.\n\n"
    else:
        report += "⚠️ *Topic analysis unavailable - API key may not be configured*\n\n"
    
    report += "---\n\n"
    
    # Step 4: Content Gap Analysis
    report += "## 🔍 Content Gap & Opportunity Analysis\n\n"
    content_analysis = analyze_video_content_with_llm(videos)
    
    if content_analysis and not ("error" in content_analysis.lower() or "failed" in content_analysis.lower()):
        report += content_analysis + "\n\n"
    else:
        report += "⚠️ *Detailed analysis unavailable - API key may not be configured*\n\n"
    
    # Step 5: Action Items
    report += "---\n\n"
    report += "## 🚀 Recommended Actions\n\n"
    
    if len(videos) > 0:
        report += "### Content Strategy:\n"
        report += f"1. **Market Size:** {len(videos)} videos found suggests {'high competition' if len(videos) >= 6 else 'moderate competition'} in this space\n"
        report += "2. **Differentiation:** Focus on unique angles identified in the gap analysis above\n"
        report += "3. **Title Strategy:** Consider variations of the successful patterns identified\n"
        report += "4. **Content Quality:** Aim to provide more comprehensive coverage than existing content\n\n"
        
        report += "### Next Steps:\n"
        report += "- Research specific subtopics with lower competition\n"
        report += "- Analyze audience engagement metrics for top performers\n"
        report += "- Consider collaboration opportunities with established creators\n"
        report += "- Plan content series around identified gaps\n\n"
    
    report += "---\n\n"
    report += "*Report generated by AI Mechanic Market Tools*"
    
    return report
    

