#!/usr/bin/env python3

import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from chroma_storage import ChromaStorage

def main():
    print("=== ChromaDB Storage Demo ===\n")
    
    # Setup paths
    research_folder = Path(__file__).parent.parent / "research_sources"
    db_path = Path(__file__).parent / "demo_chroma_db"
    
    print(f"Research folder: {research_folder}")
    print(f"Database path: {db_path}")
    print(f"Available: {ChromaStorage('dummy').is_available()}")
    print()
    
    # Initialize storage
    print("1. Initializing ChromaStorage...")
    storage = ChromaStorage(str(research_folder), str(db_path))
    
    if not storage.is_available():
        print("❌ ChromaDB not available. Install with: pip install chromadb")
        return
    
    print("✅ ChromaDB initialized successfully\n")
    
    # Load documents
    print("2. Loading documents from research_sources...")
    success = storage.load_documents()
    
    if success:
        print("✅ Documents loaded successfully\n")
    else:
        print("❌ Failed to load documents\n")
        return
    
    # Demo queries
    demo_queries = [
        {
            "query": "artificial intelligence applications",
            "topic": "AI and machine learning",
            "description": "Search for AI applications and use cases"
        },
        {
            "query": "climate change effects",
            "topic": "environmental science",
            "description": "Find information about climate change impacts"
        },
        {
            "query": "space exploration missions",
            "topic": "astronomy and space",
            "description": "Look for space exploration content"
        },
        {
            "query": "mercury planet characteristics",
            "topic": "planetary science",
            "description": "Find details about Mercury planet"
        }
    ]
    
    print("3. Demonstrating search functionality...\n")
    
    for i, demo in enumerate(demo_queries, 1):
        print(f"--- Query {i}: {demo['description']} ---")
        print(f"Query: '{demo['query']}'")
        print(f"Topic Context: '{demo['topic']}'")
        print()
        
        # Basic search
        results = storage.search(demo['query'], demo['topic'], n_results=3)
        
        if results:
            print(f"Found {len(results)} results:")
            for j, result in enumerate(results, 1):
                source_name = Path(result['source']).name
                content_preview = result['content'][:150] + "..." if len(result['content']) > 150 else result['content']
                print(f"  {j}. Source: {source_name}")
                print(f"     Preview: {content_preview}")
                if result.get('distance'):
                    print(f"     Similarity: {1 - result['distance']:.3f}")
                print()
        else:
            print("No results found.")
        
        print("-" * 60)
        print()
    
    print("4. Demonstrating LLM context formatting...\n")
    
    # Show formatted context for LLM
    query = "How does artificial intelligence work?"
    topic = "AI fundamentals"
    
    print(f"Query: '{query}'")
    print(f"Topic: '{topic}'")
    print("\nFormatted context for LLM:")
    print("=" * 40)
    
    context = storage.get_context_for_llm(query, topic, max_context_length=2000)
    
    if context:
        print(context)
    else:
        print("No context generated.")
    
    print("=" * 40)
    print()
    
    print("5. Demonstrating quick answer functionality...\n")
    
    quick_questions = [
        {
            "question": "What is artificial intelligence?",
            "context": "AI basics"
        },
        {
            "question": "How does climate change affect the environment?",
            "context": "environmental impacts"
        },
        {
            "question": "What are the goals of space exploration?",
            "context": "space science"
        }
    ]
    
    for question_data in quick_questions:
        print(f"Getting quick answer for: '{question_data['question']}'")
        print("-" * 50)
        
        answer = storage.get_quick_answer(
            question_data['question'], 
            question_data['context']
        )
        
        print(answer)
        print("\n" + "=" * 60 + "\n")
    
    print("6. Collection statistics...")
    try:
        count = storage.collection.count()
        print(f"Total chunks in database: {count}")
    except Exception as e:
        print(f"Could not get count: {e}")
    
    print("\n=== Demo Complete ===")
    print("\nTo use in your own code:")
    print("```python")
    print("from src.chroma_storage import ChromaStorage")
    print("")
    print("storage = ChromaStorage('path/to/docs')")
    print("storage.load_documents()")
    print("results = storage.search('your query', 'topic context')")
    print("context = storage.get_context_for_llm('query', 'topic')")
    print("answer = storage.get_quick_answer('question', 'context')")
    print("```")


if __name__ == "__main__":
    main()