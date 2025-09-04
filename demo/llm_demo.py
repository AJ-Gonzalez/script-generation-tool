import os
import sys
import logging

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from llm_handler import LLMHandler
from chroma_storage import ChromaStorage

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    print("=== LLM Handler with ChromaDB Tool Integration Demo ===\n")
    
    # Set up ChromaDB
    research_sources_path = os.path.join(os.path.dirname(__file__), '..', 'research_sources')
    chroma_db_path = os.path.join(os.path.dirname(__file__), '..', 'chroma_db')
    
    print("Initializing ChromaDB storage...")
    chroma_storage = ChromaStorage(research_sources_path, chroma_db_path)
    
    if not chroma_storage.is_available():
        print("❌ ChromaDB not available. Please install with: pip install chromadb")
        return
    
    # Load documents into ChromaDB
    print("Loading documents into ChromaDB...")
    if chroma_storage.load_documents():
        print("✅ Documents loaded successfully!\n")
    else:
        print("❌ Failed to load documents\n")
        return
    
    # Initialize LLM handler with ChromaDB
    print("Initializing LLM handler...")
    try:
        llm_handler = LLMHandler(chroma_storage)
        print("✅ LLM handler initialized successfully!\n")
    except Exception as e:
        print(f"❌ Failed to initialize LLM handler: {e}")
        return
    
    # Demo examples
    examples = [
        {
            "query": "What are the main benefits of renewable energy?",
            "description": "Query about renewable energy benefits - should trigger tool search"
        },
        {
            "query": "Tell me about space exploration missions",
            "description": "Query about space exploration - should search knowledge base"
        },
        {
            "query": "How does artificial intelligence impact elections?",
            "description": "Query about AI and elections - should find relevant documents"
        }
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"=== Example {i}: {example['description']} ===")
        print(f"Query: {example['query']}\n")
        
        try:
            response = llm_handler.prompt_ai(example['query'])
            print("AI Response:")
            print("-" * 50)
            print(response)
            print("-" * 50)
            print()
            
        except Exception as e:
            print(f"❌ Error processing query: {e}\n")
        
        # Add pause between examples
        if i < len(examples):
            input("Press Enter to continue to next example...")
            print()
    
    # Interactive mode
    print("=== Interactive Mode ===")
    print("You can now ask questions. The AI will search the knowledge base automatically.")
    print("Type 'quit' to exit.\n")
    
    while True:
        try:
            user_input = input("Your question: ").strip()
            if user_input.lower() in ['quit', 'exit', 'q']:
                break
            
            if not user_input:
                continue
                
            print("\nAI Response:")
            print("-" * 50)
            response = llm_handler.prompt_ai(user_input)
            print(response)
            print("-" * 50)
            print()
            
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"❌ Error: {e}\n")

if __name__ == "__main__":
    main()