"""
Demo script for search term generation functionality.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from context_engine import generate_search_terms
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def demo_search_terms():
    """Demonstrate search term generation for various topics."""
    
    test_topics = [
        "Artificial Intelligence",
        "Climate Change",
        "Quantum Computing",
        "Space Exploration",
        "Renewable Energy"
    ]
    
    print("=== Search Terms Generation Demo ===\n")
    
    for topic in test_topics:
        print(f"Topic: {topic}")
        try:
            search_terms = generate_search_terms(topic)
            print(f"Generated search terms: {search_terms}")
        except Exception as e:
            logger.error(f"Error generating search terms for '{topic}': {e}")
            print(f"Error: {e}")
        print("-" * 50)

if __name__ == "__main__":
    demo_search_terms()