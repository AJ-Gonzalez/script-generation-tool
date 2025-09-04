#!/usr/bin/env python3
"""
Demo script for market_tools.py functions.
Shows how to use YouTube search and analysis functions for market research.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from market_tools import (
    search_youtube_videos,
    analyze_video_content_with_llm,
    extract_title_patterns,
    analyze_video_topics
)

def print_separator(title):
    """Print a visual separator for demo sections."""
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)

def print_list_results(title, items):
    """Print list results in a nice format."""
    print(f"\n{title}:")
    print("-" * len(title))
    for i, item in enumerate(items, 1):
        print(f"{i}. {item}")

def demo_market_tools(topic):
    """
    Demonstrate all market_tools functions with a given topic.
    """
    print(f"🎯 Market Research Demo for Topic: '{topic}'")
    print("This demo will show you insights from YouTube content analysis.")
    
    # Step 1: Search YouTube videos
    print_separator("Step 1: Searching YouTube Videos")
    print(f"Searching for top 8 videos about '{topic}'...")
    
    videos = search_youtube_videos(topic, max_results=8)
    
    if not videos:
        print("❌ Failed to fetch videos.")
        print("This could be due to:")
        print("1. yt-dlp not installed - run: pip install yt-dlp")
        print("2. yt-dlp not in PATH")
        print("3. Network connectivity issues")
        return
    
    if isinstance(videos, list) and len(videos) > 0 and "API key not configured" in str(videos[0]):
        print("❌ Failed to fetch videos. Check your OPENROUTER_API_KEY.")
        return
    
    print(f"✅ Found {len(videos)} videos!")
    
    # Show video summaries
    print("\nVideo Summaries:")
    print("-" * 20)
    for i, video in enumerate(videos, 1):
        print(f"\n{i}. {video['title']}")
        print(f"   Views: {video['view_count']} | Duration: {video['duration']}")
        print(f"   Description: {video['description'][:100]}{'...' if len(video['description']) > 100 else ''}")
    
    # Step 2: Extract title patterns
    print_separator("Step 2: Analyzing Title Patterns")
    print("Analyzing common patterns in video titles...")
    
    patterns = extract_title_patterns(videos)
    print_list_results("Common Title Patterns Found", patterns)
    
    # Step 3: Analyze topics covered
    print_separator("Step 3: Identifying Topics Covered")
    print("Analyzing what topics are being discussed...")
    
    topics = analyze_video_topics(videos)
    print_list_results("Topics Being Covered", topics)
    
    # Step 4: Comprehensive content analysis
    print_separator("Step 4: Content Gap Analysis")
    print("Analyzing content themes and identifying opportunities...")
    
    analysis = analyze_video_content_with_llm(videos)
    print("\nDetailed Analysis:")
    print("-" * 20)
    print(analysis)
    
    # Summary
    print_separator("Demo Complete!")
    print("📊 Market Research Summary:")
    print(f"• Found {len(videos)} videos on '{topic}'")
    print(f"• Identified {len(patterns)} common title patterns")
    print(f"• Discovered {len(topics)} main topic areas")
    print("• Generated comprehensive gap analysis")
    print("\n💡 Use these insights to create unique, differentiated content!")

def main():
    """Main demo function with user input."""
    print("🚀 Welcome to Market Tools Demo!")
    print("This tool helps you analyze YouTube content for any topic.")
    
    # Get topic from user
    topic = input("\nEnter a topic to research (e.g. 'AI automation', 'healthy cooking'): ").strip()
    
    if not topic:
        print("❌ No topic provided. Exiting.")
        return
    
    try:
        demo_market_tools(topic)
    except Exception as e:
        print(f"❌ Demo failed: {str(e)}")
        print("Make sure you have:")
        print("1. yt-dlp installed: pip install yt-dlp")
        print("2. OPENROUTER_API_KEY set in your environment")
        print("3. Internet connection for API calls")
        print("4. yt-dlp accessible in PATH")

if __name__ == "__main__":
    main()