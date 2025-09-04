#!/usr/bin/env python3
"""
Alternative demo script for market_tools.py functions.
Runs analysis on predefined test topics and saves results to JSON.
"""

import sys
import os
import json
from datetime import datetime
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from market_tools import (
    search_youtube_videos,
    analyze_video_content_with_llm,
    extract_title_patterns,
    analyze_video_topics
)

test_topics = [
   # Oversaturated markets
   "how to make money online",
   "iPhone review", 
   "weight loss tips",
   "Minecraft gameplay",
   
   # Niche/specialized topics
   "quantum computing explained",
   "beekeeping for beginners",
   "medieval manuscript illumination",
   "tax law changes 2025",
   
   # Current events/trending
   "AI regulation news",
   "cryptocurrency market analysis", 
   "climate change solutions",
   
   # Controversial/opinion-heavy
   "best programming language 2025",
   "is college worth it",
   "remote work vs office work",
   
   # Very specific technical
   "Docker container orchestration",
   "CRISPR gene editing ethics",
   "solar panel installation guide",
   
   # Weird edge cases
   "history of left-handed scissors",
   "why cats purr scientific explanation",
   "competitive eating techniques"
]

def analyze_topic(topic):
    """
    Analyze a single topic and return structured results.
    """
    print(f"🔍 Analyzing: {topic}")
    
    # Search for videos
    videos = search_youtube_videos(topic, max_results=6)
    
    if not videos or (isinstance(videos, list) and len(videos) > 0 and "API key not configured" in str(videos[0])):
        return {
            "topic": topic,
            "status": "failed",
            "error": "Failed to fetch videos or API key not configured",
            "videos": [],
            "title_patterns": [],
            "topics_covered": [],
            "content_analysis": "Analysis unavailable"
        }
    
    print(f"   ✅ Found {len(videos)} videos")
    
    # Extract title patterns
    print("   📊 Analyzing title patterns...")
    patterns = extract_title_patterns(videos)
    
    # Analyze topics covered
    print("   🏷️ Identifying topics...")
    topics_covered = analyze_video_topics(videos)
    
    # Comprehensive content analysis
    print("   🧠 Running LLM analysis...")
    content_analysis = analyze_video_content_with_llm(videos)
    
    return {
        "topic": topic,
        "status": "success",
        "video_count": len(videos),
        "videos": videos,
        "title_patterns": patterns,
        "topics_covered": topics_covered,
        "content_analysis": content_analysis
    }

def run_batch_analysis():
    """
    Run analysis on all test topics and save to JSON.
    """
    print("🚀 Starting Batch Market Research Analysis")
    print(f"📋 Analyzing {len(test_topics)} topics...")
    
    results = {
        "analysis_date": datetime.now().isoformat(),
        "total_topics": len(test_topics),
        "results": {}
    }
    
    successful_analyses = 0
    failed_analyses = 0
    
    for i, topic in enumerate(test_topics, 1):
        print(f"\n[{i}/{len(test_topics)}] Processing: {topic}")
        
        try:
            topic_result = analyze_topic(topic)
            results["results"][topic] = topic_result
            
            if topic_result["status"] == "success":
                successful_analyses += 1
            else:
                failed_analyses += 1
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            results["results"][topic] = {
                "topic": topic,
                "status": "error",
                "error": str(e),
                "videos": [],
                "title_patterns": [],
                "topics_covered": [],
                "content_analysis": "Analysis failed due to error"
            }
            failed_analyses += 1
    
    # Add summary statistics
    results["summary"] = {
        "successful_analyses": successful_analyses,
        "failed_analyses": failed_analyses,
        "success_rate": f"{(successful_analyses / len(test_topics)) * 100:.1f}%"
    }
    
    # Save to JSON file
    output_file = "market_research_batch_results.json"
    output_path = os.path.join(os.path.dirname(__file__), output_file)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n🎉 Analysis Complete!")
    print(f"📊 Summary:")
    print(f"   • Successful: {successful_analyses}")
    print(f"   • Failed: {failed_analyses}")
    print(f"   • Success Rate: {results['summary']['success_rate']}")
    print(f"📄 Results saved to: {output_path}")
    
    return results

def main():
    """Main function for batch analysis."""
    print("🔬 Market Tools Batch Analysis Demo")
    print("This will analyze all predefined test topics and save results to JSON.")
    
    response = input("\nStart batch analysis? This may take several minutes. (y/n): ").strip().lower()
    
    if response != 'y':
        print("❌ Analysis cancelled.")
        return
    
    try:
        results = run_batch_analysis()
        
        # Print some interesting insights
        print(f"\n💡 Quick Insights:")
        successful_topics = [topic for topic, data in results["results"].items() if data["status"] == "success"]
        
        if successful_topics:
            print(f"   • Topics with most videos found:")
            video_counts = [(topic, data["video_count"]) for topic, data in results["results"].items() if data["status"] == "success"]
            video_counts.sort(key=lambda x: x[1], reverse=True)
            
            for topic, count in video_counts[:3]:
                print(f"     - {topic}: {count} videos")
        
    except Exception as e:
        print(f"❌ Batch analysis failed: {str(e)}")
        print("Make sure you have:")
        print("1. yt-dlp installed: pip install yt-dlp")
        print("2. OPENROUTER_API_KEY set in your environment")
        print("3. Internet connection for API calls")

if __name__ == "__main__":
    main()