"""
Demo script for process_topic_and_keypoints functionality.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from context_engine import process_topic_and_keypoints
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def demo_topic_keypoints():
    """Demonstrate topic and keypoints processing."""
    
    test_cases = [
        {
            "general_topic": "Artificial Intelligence",
            "key_points": """• Machine learning algorithms for pattern recognition
- Neural networks and deep learning architectures
→ Natural language processing capabilities
* Computer vision applications
1. Ethical considerations in AI development
2. AI bias and fairness issues
▪ Automated decision making systems
- Future of work and AI automation"""
        },
        {
            "general_topic": "Climate Change",
            "key_points": """1. Rising global temperatures and greenhouse gases
• Melting ice caps and sea level rise
- Extreme weather events becoming more frequent
→ Impact on biodiversity and ecosystems
* Renewable energy transition strategies
2. Carbon capture and storage technologies
‣ International climate agreements and policies
- Economic implications of climate action"""
        },
        {
            "general_topic": "Space Exploration",
            "key_points": """Mars colonization missions and challenges
• Satellite technology and communication systems
- International Space Station research projects
1. Commercial spaceflight industry growth
→ Search for extraterrestrial life
* Asteroid mining potential and resources
2. Space debris and orbital pollution
▫ Lunar base development plans"""
        }
    ]
    
    print("=== Topic and Key Points Processing Demo ===\n")
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"--- Test Case {i} ---")
        print(f"General Topic: {test_case['general_topic']}")
        print(f"Key Points Input:\n{test_case['key_points']}")
        print()
        
        try:
            search_terms, topic, parsed_points = process_topic_and_keypoints(
                test_case['general_topic'], 
                test_case['key_points']
            )
            
            print(f"Combined Search Terms ({len(search_terms)} total):")
            for j, term in enumerate(search_terms, 1):
                print(f"  {j}. {term}")
            
            print(f"\nGeneral Topic: {topic}")
            
            print(f"\nParsed Key Points ({len(parsed_points)} statements):")
            for j, point in enumerate(parsed_points, 1):
                print(f"  {j}. {point}")
                
        except Exception as e:
            logger.error(f"Error processing test case {i}: {e}")
            print(f"Error: {e}")
        
        print("=" * 60)
        print()

if __name__ == "__main__":
    demo_topic_keypoints()