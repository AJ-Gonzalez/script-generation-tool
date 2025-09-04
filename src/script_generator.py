
import os
import logging
from pathlib import Path
from typing import List
from context_engine import research_with_wikipedia
from chroma_storage import ChromaStorage
from llm_handler import LLMHandler
import requests
import json
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('OPENROUTER_API_KEY')

logger = logging.getLogger(__name__)

def generate_research_summary_with_llm(content: str, topic: str, summary_type: str) -> str:
    """
    Use a cost-effective LLM call to generate research summaries.
    
    Args:
        content: Raw content to summarize
        topic: Main topic for context
        summary_type: Type of summary (key_facts, context, angles, etc.)
        
    Returns:
        Generated summary text
    """
    if not api_key or not content.strip():
        return f"Information about {topic} from research database."
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    if summary_type == "key_facts":
        prompt = f"Extract 3-5 key facts about {topic} from this content. Return as bullet points:\n\n{content[:800]}"
    elif summary_type == "context":
        prompt = f"Write 2-3 sentences explaining the background context of {topic} based on this content:\n\n{content[:800]}"
    elif summary_type == "angles":
        prompt = f"List 3-4 different approaches or perspectives related to {topic} from this content. Return as bullet points:\n\n{content[:800]}"
    elif summary_type == "related_topics":
        prompt = f"List 5-6 related topics that are relevant to {topic}. Include subtopics, related fields, and adjacent areas of interest. Return as bullet points with just the topic names (no descriptions):\n\nExample for 'Artificial Intelligence':\n- Machine Learning\n- Neural Networks\n- Natural Language Processing\n- Computer Vision\n- Robotics\n- Data Science\n\nNow generate related topics for: {topic}"
    else:
        prompt = f"Summarize information about {topic} from this content in 2-3 sentences:\n\n{content[:800]}"
    
    data = {
        "model": "openai/gpt-3.5-turbo",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 150,
        "temperature": 0.3
    }
    
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=15
        )
        response.raise_for_status()
        result = response.json()
        return result['choices'][0]['message']['content'].strip()
    except Exception as e:
        logger.warning(f"LLM summary failed for {summary_type}: {e}")
        return f"Research information about {topic} from knowledge database."

def extract_research_data_for_ui(main_topic: str, key_points: List[str], chroma_storage: ChromaStorage, research_results: dict) -> dict:
    """
    Extract and organize research data for the UI research panel.
    
    Args:
        main_topic: Main topic for research
        key_points: List of key points
        chroma_storage: ChromaDB storage instance
        research_results: Wikipedia research results
        
    Returns:
        Dictionary with organized research data for UI
    """
    # Extract key facts using ChromaDB and LLM summarization
    key_facts = []
    key_facts_query = f"key facts about {main_topic}"
    key_facts_results = chroma_storage.search(key_facts_query, main_topic, n_results=3)
    
    if key_facts_results:
        # Combine content from search results
        combined_content = "\n\n".join([result['content'] for result in key_facts_results[:2]])
        # Use cost-effective LLM to extract key facts
        key_facts_text = generate_research_summary_with_llm(combined_content, main_topic, "key_facts")
        # Parse bullet points from LLM response
        for line in key_facts_text.split('\n'):
            line = line.strip().lstrip('•-* ')
            if line and len(line) > 10:
                key_facts.append(line)
                if len(key_facts) >= 5:
                    break
    
    # Extract context and background using ChromaDB and LLM summarization
    context_query = f"background context history of {main_topic}"
    context_results = chroma_storage.search(context_query, main_topic, n_results=2)
    
    if context_results:
        # Combine content from search results
        combined_content = "\n\n".join([result['content'] for result in context_results])
        # Use cost-effective LLM to generate context summary
        context = generate_research_summary_with_llm(combined_content, main_topic, "context")
    else:
        context = f"Background information about {main_topic} from research database."
    
    # Extract different angles using ChromaDB and LLM summarization
    angles = []
    angles_query = f"different perspectives approaches to {main_topic}"
    angles_results = chroma_storage.search(angles_query, main_topic, n_results=3)
    
    if angles_results:
        # Combine content from search results
        combined_content = "\n\n".join([result['content'] for result in angles_results])
        # Use cost-effective LLM to extract different angles
        angles_text = generate_research_summary_with_llm(combined_content, main_topic, "angles")
        # Parse bullet points from LLM response
        for line in angles_text.split('\n'):
            line = line.strip().lstrip('•-* ')
            if line and len(line) > 15:
                angles.append(line)
                if len(angles) >= 4:
                    break
    
    if not angles:
        angles = [f"Multiple approaches to understanding {main_topic}", f"Various applications of {main_topic}", f"Different aspects of {main_topic}"]
    
    # Generate related topics using cost-effective LLM
    related_topics = []
    related_topics_text = generate_research_summary_with_llm("", main_topic, "related_topics")
    
    # Parse the LLM response into individual topics
    if related_topics_text and "error" not in related_topics_text.lower():
        for line in related_topics_text.split('\n'):
            line = line.strip().lstrip('•-* ')
            if line and len(line) > 3 and len(line) < 60:
                # Clean up common artifacts
                line = line.strip('.,;:')
                if line.lower() != main_topic.lower():
                    related_topics.append(line)
                if len(related_topics) >= 6:
                    break
    
    # Fallback to search terms if LLM fails
    if len(related_topics) < 3:
        search_terms = research_results.get('search_terms', [])
        for term in search_terms[1:]:  # Skip the main topic
            if term.lower() != main_topic.lower() and term not in related_topics:
                related_topics.append(term.title())
                if len(related_topics) >= 6:
                    break
    
    # Extract articles/sources
    articles = []
    wikipedia_results = research_results.get('wikipedia_results', {})
    for term, result in wikipedia_results.items():
        if 'error' not in result and 'title' in result:
            articles.append({
                'title': result['title'],
                'url': result.get('url', f"https://en.wikipedia.org/wiki/{result['title'].replace(' ', '_')}")
            })
        if len(articles) >= 5:
            break
    
    return {
        'key_facts': key_facts[:5] if key_facts else [f"Research data about {main_topic} from knowledge base"],
        'context': context[:500] + '...' if len(context) > 500 else context,
        'angles': angles[:4] if angles else [f"Different approaches to {main_topic}"],
        'related_topics': related_topics[:6] if related_topics else [f"Topics related to {main_topic}"],
        'articles': articles
    }


def generate_script_with_llm(brand_name: str, we_focus_on: str, main_topic: str, key_points: List[str], tone: str, target_runtime: int) -> tuple[str, dict]:
    """
    Generate a video script using LLM with research backing from Wikipedia and ChromaDB.
    
    Args:
        brand_name: Name of the brand
        we_focus_on: What the brand focuses on
        main_topic: Main topic for the script
        key_points: List of key points to cover
        tone: Tone of the script
        target_runtime: Target runtime in minutes
        
    Returns:
        Tuple of (Generated script as markdown string, research data for UI)
    """
    logger.info(f"Starting script generation for topic: {main_topic}")
    
    # Convert key_points list to bullet point string for research
    key_points_text = "\n".join([f"- {point}" for point in key_points])
    
    # Step 1: Research topic and key points using Wikipedia
    logger.info("Conducting research using Wikipedia...")
    research_results = research_with_wikipedia(main_topic, key_points_text)
    
    # Step 2: Initialize ChromaDB and load any new research
    research_sources_path = Path(__file__).parent.parent / "research_sources"
    chroma_db_path = Path(__file__).parent.parent / "chroma_db"
    
    logger.info("Initializing ChromaDB storage...")
    chroma_storage = ChromaStorage(str(research_sources_path), str(chroma_db_path))
    
    if not chroma_storage.is_available():
        logger.error("ChromaDB not available - install with: pip install chromadb")
        raise RuntimeError("ChromaDB is required for script generation")
    
    # Load/reload documents to include any new research
    logger.info("Loading documents into ChromaDB...")
    if not chroma_storage.load_documents():
        logger.warning("Failed to load documents into ChromaDB")
    
    # Step 3: Initialize LLM handler with ChromaDB
    logger.info("Initializing LLM handler...")
    llm_handler = LLMHandler(chroma_storage)
    
    # Step 4: Create comprehensive prompt template
    prompt_template = f"""You are a script writer for {brand_name} which focuses on {we_focus_on}.

    Your job is to draft a video script following these specifications:

    **Topic:** {main_topic}
    **Key Points to Cover:**
    {" - "+chr(10)+" - ".join(key_points)}
    **Tone:** {tone}
    **Target Runtime:** {target_runtime} minutes

    **IMPORTANT - Research Process:**
    Before writing each section, actively search the knowledge base for relevant information. Use the search_knowledge tool to find:
    - Facts, statistics, and data points
    - Background context and explanations
    - Different perspectives or angles
    - Supporting evidence for claims

    Search multiple times with different queries as you work through each key point. Always cite your sources when you use information from the knowledge base.

    **Writing Style Guidelines:**
    - Use contractions and casual language
    - Include transition phrases like "here's the thing," "so," "what's interesting is"
    - Ask rhetorical questions to engage viewers
    - Be helpful but not overly formal
    - Sound natural and conversational
    - Match the specified tone: {tone}

    **Research Context Available:**
    Recent research was conducted on: {', '.join(research_results.get('search_terms', [])[:5])}
    
    Write a complete script that covers all key points with proper research backing. Structure it for a {target_runtime}-minute video with natural pacing and smooth transitions between topics.
    
    Format the output as a markdown document with:
    - Clear section headers
    - Natural speaking flow
    - Source citations when using researched information
    - Estimated timing for each section
    """
    
    # Step 5: Generate script using LLM
    logger.info("Generating script with LLM...")
    try:
        script = llm_handler.prompt_ai(prompt_template)
        
        # Step 6: Save script as markdown file
        scripts_dir = Path(__file__).parent.parent / "generated_scripts"
        scripts_dir.mkdir(exist_ok=True)
        
        # Create safe filename
        safe_topic = "".join(c for c in main_topic if c.isalnum() or c in (' ', '-', '_')).rstrip()
        filename = f"script_{safe_topic.lower().replace(' ', '_')}.md"
        script_path = scripts_dir / filename
        
        # Add metadata header to script
        script_with_metadata = f"""# Video Script: {main_topic}

**Brand:** {brand_name}
**Focus:** {we_focus_on}
**Tone:** {tone}
**Target Runtime:** {target_runtime} minutes
**Generated:** {research_results.get('successful_searches', 0)}/{research_results.get('total_searches', 0)} research sources

---

{script}
"""
        
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_with_metadata)
        
        logger.info(f"Script saved to: {script_path}")
        
        # Step 7: Extract research data for UI
        logger.info("Extracting research data for UI...")
        research_data = extract_research_data_for_ui(main_topic, key_points, chroma_storage, research_results)
        
        return script_with_metadata, research_data
        
    except Exception as e:
        logger.error(f"Failed to generate script: {e}")
        raise RuntimeError(f"Script generation failed: {e}")
    
    finally:
        # Log research summary
        if research_results:
            logger.info(f"Research summary: {research_results.get('successful_searches', 0)} successful searches out of {research_results.get('total_searches', 0)} terms")