#!/usr/bin/env python3

import sys
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

from wikipeda_scraper import WikipediaScraper
import json
import time

def demo_basic_search():
    """Basic usage example - search for a topic"""
    print("=" * 50)
    print("DEMO 1: Basic Wikipedia Search")
    print("=" * 50)
    
    scraper = WikipediaScraper(delay=1.0)
    
    # Search for Climate Change
    print("Searching for 'Climate Change'...")
    result = scraper.search_article("Climate Change")
    
    if "error" in result:
        print(f"Error: {result['error']}")
        return
    
    print(f"\nTitle: {result['title']}")
    print(f"URL: {result['url']}")
    print(f"\nContext & Background:\n{result['context_background'][:200]}...")
    
    print(f"\nKey Facts Found ({len(result['key_facts'])}):")
    for i, fact in enumerate(result['key_facts'][:3], 1):
        print(f"  {i}. {fact}")
    
    print(f"\nMain Sections ({len(result['different_angles'])}):")
    for section in result['different_angles'][:3]:
        print(f"  • {section['heading']}")
    
    print(f"\nRelated Topics ({len(result['related_topics'])}):")
    for topic in result['related_topics']:
        print(f"  • {topic['title']}")
    
    print(f"\nFiles saved to: research_sources/")
    print(f"Total sources: {len(result['sources'])}")

def demo_disambiguation_handling():
    """Demo disambiguation page handling"""
    print("\n" + "=" * 50)
    print("DEMO 2: Disambiguation Page Handling")
    print("=" * 50)
    
    scraper = WikipediaScraper(delay=1.5)
    
    # Search for "Mercury" - a disambiguation case
    print("Searching for 'Mercury' (disambiguation case)...")
    result = scraper.search_article("Mercury")
    
    if "error" in result:
        print(f"Error: {result['error']}")
        return
    
    print(f"\nResolved to: {result['title']}")
    print(f"Summary: {result['context_background'][:300]}...")
    
    print(f"\nKey facts extracted:")
    for fact in result['key_facts'][:2]:
        print(f"  • {fact}")

def demo_edge_case():
    """Demo edge case handling (no results)"""
    print("\n" + "=" * 50)
    print("DEMO 3: Edge Case - No Results")
    print("=" * 50)
    
    scraper = WikipediaScraper()
    
    # Search for something that doesn't exist
    print("Searching for 'XyzNonExistentTopic123'...")
    result = scraper.search_article("XyzNonExistentTopic123")
    
    if "error" in result:
        print(f"Handled gracefully: {result['error']}")
    else:
        print("Unexpected success - this should have failed!")

def demo_research_dossier_format():
    """Show the complete research dossier format"""
    print("\n" + "=" * 50)
    print("DEMO 4: Research Dossier Format")
    print("=" * 50)
    
    scraper = WikipediaScraper(delay=1.0)
    
    print("Searching for 'Artificial Intelligence'...")
    result = scraper.search_article("Artificial Intelligence")
    
    if "error" in result:
        print(f"Error: {result['error']}")
        return
    
    # Show complete structure
    print("\nComplete Research Dossier Structure:")
    print(f"├── Title: {result['title']}")
    print(f"├── URL: {result['url']}")
    print(f"├── Key Facts: {len(result['key_facts'])} items")
    print(f"├── Context & Background: {len(result['context_background'])} chars")
    print(f"├── Different Angles: {len(result['different_angles'])} sections")
    print(f"├── Related Topics: {len(result['related_topics'])} articles")
    print(f"└── Sources: {len(result['sources'])} URLs")
    
    # Show improved key facts
    print("\nSample Key Facts (now human-readable):")
    for i, fact in enumerate(result['key_facts'][:3], 1):
        print(f"  {i}. {fact}")
    
    # Save formatted JSON for inspection
    output_file = Path("demo") / "sample_research_dossier.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"\nFull dossier saved to: {output_file}")

def demo_markdown_dossier():
    """Demo the new markdown dossier with images"""
    print("\n" + "=" * 50)
    print("DEMO 5: Enhanced Markdown Dossier")
    print("=" * 50)
    
    scraper = WikipediaScraper(delay=1.0)
    
    print("Generating improved markdown dossier for 'Artificial Intelligence'...")
    markdown_content = scraper.generate_markdown_dossier("Artificial Intelligence")
    
    # Save the markdown dossier
    output_file = Path("demo") / "ai_dossier_improved.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
    
    print(f"Enhanced markdown dossier saved to: {output_file}")
    
    # Show key facts section specifically
    key_facts_start = markdown_content.find("## Key Facts & Figures")
    detailed_start = markdown_content.find("## Detailed Analysis")
    
    if key_facts_start != -1 and detailed_start != -1:
        key_facts_section = markdown_content[key_facts_start:detailed_start].strip()
        print("\nKey Facts section (now clean and bullet-pointed):")
        print("-" * 40)
        print(key_facts_section)
        print("-" * 40)
    
    print("\nImprovements made:")
    print("  ✓ No more 'Fact 1, Fact 2' numbering")
    print("  ✓ Clean bullet points with meaningful content")
    print("  ✓ Removed HTML artifacts and citations")
    print("  ✓ Complete sentences from summary prioritized")
    print("  ✓ Better filtering of junk content")

def demo_key_facts_improvement():
    """Demo the improved key facts extraction"""
    print("\n" + "=" * 50)
    print("DEMO 6: Improved Key Facts Extraction")
    print("=" * 50)
    
    scraper = WikipediaScraper(delay=1.0)
    
    print("Testing key facts extraction on 'Climate Change'...")
    result = scraper.search_article("Climate Change")
    
    if "error" in result:
        print(f"Error: {result['error']}")
        return
    
    print("\nExtracted Key Facts (clean, human-readable):")
    for i, fact in enumerate(result['key_facts'], 1):
        print(f"\n{i}. {fact}")
    
    print(f"\nTotal facts extracted: {len(result['key_facts'])}")
    print("Note: Facts are now cleaned of HTML and provide meaningful context!")

def main():
    """Run all demo examples"""
    print("Wikipedia Scraper Demo - Enhanced Edition")
    print("This demo showcases the WikipediaScraper capabilities")
    print("Note: Requests are rate-limited, so demos may take time...\n")
    
    try:
        demo_basic_search()
        time.sleep(2)  # Brief pause between demos
        
        demo_disambiguation_handling()
        time.sleep(2)
        
        demo_edge_case()
        time.sleep(2)
        
        demo_research_dossier_format()
        time.sleep(2)
        
        demo_key_facts_improvement()
        time.sleep(2)
        
        demo_markdown_dossier()
        
    except KeyboardInterrupt:
        print("\nDemo interrupted by user")
    except Exception as e:
        print(f"\nDemo failed with error: {e}")
    
    print("\n" + "=" * 50)
    print("Demo completed! Check the research_sources/ and demo/ folders for output files.")
    print("New features demonstrated:")
    print("  ✓ Human-readable key facts (no more HTML)")
    print("  ✓ Markdown dossier generation with images")
    print("  ✓ Enhanced visual presentation")
    print("=" * 50)

if __name__ == "__main__":
    main()