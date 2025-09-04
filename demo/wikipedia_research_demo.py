"""
Demo script for comprehensive Wikipedia research using context engine.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from context_engine import research_with_wikipedia
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def demo_wikipedia_research():
    """Demonstrate comprehensive Wikipedia research functionality."""
    
    test_case = {
        "general_topic": "Renewable Energy Technologies",
        "key_points": """• Solar photovoltaic systems and efficiency improvements
- Wind turbine technology and offshore installations
→ Hydroelectric power generation and environmental impact
* Battery storage solutions for renewable energy
1. Smart grid integration challenges
2. Government policies and subsidies for clean energy
▪ Geothermal energy potential and applications
- Carbon footprint reduction strategies"""
    }
    
    print("=== Wikipedia Research Demo ===\n")
    print(f"General Topic: {test_case['general_topic']}")
    print(f"Key Points:\n{test_case['key_points']}")
    print("\n" + "="*60 + "\n")
    
    try:
        # Perform comprehensive Wikipedia research
        logger.info("Starting comprehensive Wikipedia research...")
        results = research_with_wikipedia(
            test_case['general_topic'], 
            test_case['key_points']
        )
        
        # Display results summary
        print("🔍 RESEARCH SUMMARY")
        print(f"General Topic: {results['general_topic']}")
        print(f"Search Terms Generated: {len(results['search_terms'])}")
        print(f"Successful Wikipedia Searches: {results['successful_searches']}/{results['total_searches']}")
        
        print(f"\n📋 PARSED KEY POINTS ({len(results['parsed_key_points'])}):")
        for i, point in enumerate(results['parsed_key_points'], 1):
            print(f"  {i}. {point}")
        
        print(f"\n🔎 SEARCH TERMS:")
        for i, term in enumerate(results['search_terms'], 1):
            status = "✅" if term in results['wikipedia_results'] and "error" not in results['wikipedia_results'][term] else "❌"
            print(f"  {i}. {term} {status}")
        
        print(f"\n📚 WIKIPEDIA RESEARCH RESULTS:")
        for term, data in results['wikipedia_results'].items():
            if "error" in data:
                print(f"  ❌ {term}: {data['error']}")
            else:
                print(f"  ✅ {term}: '{data['title']}'")
                print(f"     Key Facts: {len(data.get('key_facts', []))}")
                print(f"     Related Topics: {len(data.get('related_topics', []))}")
                print(f"     URL: {data.get('url', 'N/A')}")
        
        print(f"\n💾 FILES GENERATED:")
        print("  • Individual article files saved to research_sources/")
        print("  • Comprehensive dossiers saved with 'dossier-' prefix")
        print("  • Check research_sources/ directory for all generated content")
        
        # Show research quality metrics
        total_facts = sum(len(data.get('key_facts', [])) for data in results['wikipedia_results'].values() if 'error' not in data)
        total_topics = sum(len(data.get('related_topics', [])) for data in results['wikipedia_results'].values() if 'error' not in data)
        
        print(f"\n📊 RESEARCH METRICS:")
        print(f"  • Total Key Facts Extracted: {total_facts}")
        print(f"  • Total Related Topics Found: {total_topics}")
        print(f"  • Research Success Rate: {results['successful_searches']}/{len(results['search_terms'])} ({100*results['successful_searches']/len(results['search_terms']):.1f}%)")
        
        # Show sample content from successful searches
        successful_results = {k: v for k, v in results['wikipedia_results'].items() if 'error' not in v}
        if successful_results:
            sample_key = list(successful_results.keys())[0]
            sample_data = successful_results[sample_key]
            
            print(f"\n📄 SAMPLE CONTENT FROM '{sample_key}':")
            print(f"Title: {sample_data['title']}")
            if sample_data.get('context_background'):
                preview = sample_data['context_background'][:200] + "..." if len(sample_data['context_background']) > 200 else sample_data['context_background']
                print(f"Summary: {preview}")
            
            if sample_data.get('key_facts'):
                print(f"Sample Key Fact: {sample_data['key_facts'][0]}")
                
    except Exception as e:
        logger.error(f"Error during Wikipedia research: {e}")
        print(f"❌ Error: {e}")
    
    print("\n" + "="*60)
    print("Demo completed! Check the research_sources/ directory for generated files.")

if __name__ == "__main__":
    demo_wikipedia_research()