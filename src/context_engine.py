from dotenv import load_dotenv
import os
import requests
import json
import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)

load_dotenv()
api_key = os.getenv('OPENROUTER_API_KEY')

def generate_search_terms(main_topic: str) -> list[str]:
    """
    Generate search terms for a given topic using OpenRouter API.
    
    Args:
        main_topic (str): The main topic to generate search terms for
        
    Returns:
        list[str]: List of search terms with main topic as first element
    """
    if not api_key:
        logger.error("OPENROUTER_API_KEY not found in environment variables")
        return [main_topic]
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    prompt = f"""Generate 5-8 relevant search terms for the topic: "{main_topic}"

Return only a JSON array of strings. Include the original topic and related terms, synonyms, and subtopics.

Example for "Artificial Intelligence":
["artificial intelligence", "machine learning", "neural networks", "deep learning", "AI algorithms", "natural language processing"]"""
    
    data = {
        "model": "openai/gpt-3.5-turbo",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 200,
        "temperature": 0.7
    }
    
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )
        response.raise_for_status()
        
        result = response.json()
        content = result['choices'][0]['message']['content'].strip()
        
        # Parse JSON response
        search_terms = json.loads(content)
        
        # Ensure main topic is first
        if main_topic not in search_terms:
            search_terms.insert(0, main_topic)
        elif search_terms[0] != main_topic:
            search_terms.remove(main_topic)
            search_terms.insert(0, main_topic)
            
        return search_terms
        
    except requests.RequestException as e:
        logger.error(f"API request failed: {e}")
        return [main_topic]
    except (json.JSONDecodeError, KeyError) as e:
        logger.error(f"Failed to parse API response: {e}")
        return [main_topic]


def extract_keywords(text: str) -> list[str]:
    """
    Extract keywords from text to become research topics.
    
    Args:
        text (str): The text to extract keywords from
        
    Returns:
        list[str]: List of unique keywords suitable for research
    """
    if not text.strip():
        return []
        
    if not api_key:
        logger.error("OPENROUTER_API_KEY not found in environment variables")
        return []
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    prompt = f"""Extract 8-12 important keywords and key phrases from this text that would make good research topics. Focus on:
- Main concepts and subjects
- Technical terms
- Important entities (people, places, organizations)
- Key themes and topics

Text: "{text[:1000]}"

Return only a JSON array of strings. Keep phrases concise (1-4 words each).

Example: ["quantum computing", "artificial intelligence", "machine learning", "neural networks"]"""
    
    data = {
        "model": "openai/gpt-3.5-turbo",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 150,
        "temperature": 0.3
    }
    
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=20
        )
        response.raise_for_status()
        
        result = response.json()
        content = result['choices'][0]['message']['content'].strip()
        
        # Parse JSON response
        keywords = json.loads(content)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_keywords = []
        for keyword in keywords:
            keyword_lower = keyword.lower().strip()
            if keyword_lower not in seen and keyword_lower:
                seen.add(keyword_lower)
                unique_keywords.append(keyword.strip())
                
        return unique_keywords
        
    except requests.RequestException as e:
        logger.error(f"API request failed: {e}")
        return []
    except (json.JSONDecodeError, KeyError) as e:
        logger.error(f"Failed to parse API response: {e}")
        return []


def combine_search_terms(main_topic: str, text: str) -> list[str]:
    """
    Combine search terms from topic generation and keyword extraction.
    
    Args:
        main_topic (str): The main topic to generate search terms for
        text (str): The text to extract keywords from
        
    Returns:
        list[str]: Combined list of unique search terms
    """
    topic_terms = generate_search_terms(main_topic)
    text_keywords = extract_keywords(text)
    
    # Combine and remove duplicates while preserving order
    seen = set()
    combined_terms = []
    
    # Add topic terms first
    for term in topic_terms:
        term_lower = term.lower().strip()
        if term_lower not in seen and term_lower:
            seen.add(term_lower)
            combined_terms.append(term.strip())
    
    # Add keywords from text
    for keyword in text_keywords:
        keyword_lower = keyword.lower().strip()
        if keyword_lower not in seen and keyword_lower:
            seen.add(keyword_lower)
            combined_terms.append(keyword.strip())
    
    return combined_terms


def process_topic_and_keypoints(general_topic: str, key_points: str) -> tuple[list[str], str, list[str]]:
    """
    Process general topic and key points to generate search terms and parsed statements.
    
    Args:
        general_topic (str): The general topic to generate search terms for
        key_points (str): Key points text (bullet points format)
        
    Returns:
        tuple: (combined_search_terms, general_topic, parsed_key_points)
    """
    # Get search terms for general topic
    topic_terms = generate_search_terms(general_topic)
    
    # Extract keywords from key points
    keypoint_keywords = extract_keywords(key_points)
    
    # Combine search terms with no duplicates
    seen = set()
    combined_terms = []
    
    # Add topic terms first
    for term in topic_terms:
        term_lower = term.lower().strip()
        if term_lower not in seen and term_lower:
            seen.add(term_lower)
            combined_terms.append(term.strip())
    
    # Add keypoint keywords
    for keyword in keypoint_keywords:
        keyword_lower = keyword.lower().strip()
        if keyword_lower not in seen and keyword_lower:
            seen.add(keyword_lower)
            combined_terms.append(keyword.strip())
    
    # Parse key points into list of statements
    parsed_points = []
    if key_points.strip():
        lines = key_points.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Remove common bullet point markers
            line = line.lstrip('•-*+→·‣▪▫◦‒–—')
            line = line.strip()
            
            # Remove numbered list markers (1. 2. etc.)
            import re
            line = re.sub(r'^\d+\.?\s*', '', line)
            line = line.strip()
            
            if line:
                parsed_points.append(line)
    
    return combined_terms, general_topic, parsed_points


def extract_broader_topics(topic: str, max_topics: int = 3) -> list[str]:
    """
    Extract broader subject topics from a specific topic using LLM.
    
    Args:
        topic (str): The specific topic to extract broader subjects from
        max_topics (int): Maximum number of broader topics to return (default: 3)
        
    Returns:
        list[str]: List of broader topics that would likely have Wikipedia articles
    """
    if not api_key:
        logger.error("OPENROUTER_API_KEY not found in environment variables")
        return []
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    prompt = f"""Extract {max_topics} broader subject topics from this specific topic that would likely have Wikipedia articles: "{topic}"

For example:
- "installing linux mint" → ["linux mint", "linux", "operating systems"]
- "AI and skill atrophy in humans" → ["artificial intelligence", "skill atrophy", "AI and human interactions"]

Return only a JSON array of strings. Focus on:
- Main subjects that are encyclopedia-worthy
- Broader categories the topic falls under
- Key concepts that would have dedicated articles

Topic: "{topic}"

Return JSON array:"""
    
    data = {
        "model": "openai/gpt-3.5-turbo",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 100,
        "temperature": 0.3
    }
    
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=20
        )
        response.raise_for_status()
        
        result = response.json()
        content = result['choices'][0]['message']['content'].strip()
        
        # Parse JSON response
        broader_topics = json.loads(content)
        
        # Limit to max_topics and filter empty strings
        filtered_topics = [topic.strip() for topic in broader_topics if topic.strip()]
        return filtered_topics[:max_topics]
        
    except requests.RequestException as e:
        logger.error(f"API request failed: {e}")
        return []
    except (json.JSONDecodeError, KeyError) as e:
        logger.error(f"Failed to parse API response: {e}")
        return []


def research_with_wikipedia(general_topic: str, key_points: str) -> dict:
    """
    Use process_topic_and_keypoints to generate search terms and research each on Wikipedia.
    
    Args:
        general_topic (str): The general topic to research
        key_points (str): Key points text (bullet points format)
        
    Returns:
        dict: Research results with search terms, topic, key points, and Wikipedia data
    """
    # Import here to avoid circular imports
    import sys
    import os
    sys.path.append(os.path.dirname(__file__))
    from wikipeda_scraper import WikipediaScraper
    
    # Get processed data
    search_terms, topic, parsed_points = process_topic_and_keypoints(general_topic, key_points)
    
    # Initialize Wikipedia scraper
    scraper = WikipediaScraper(delay=1.0)
    
    # Try to search for the main topic first to check if it has an article
    main_topic_result = scraper.search_article(general_topic)
    broader_topics_added = False
    
    # If main topic search fails, extract broader topics and add to search terms
    if "error" in main_topic_result:
        logger.info(f"Main topic '{general_topic}' not found in Wikipedia, extracting broader topics")
        broader_topics = extract_broader_topics(general_topic)
        
        if broader_topics:
            # Add broader topics to search terms while avoiding duplicates
            seen = set(term.lower().strip() for term in search_terms)
            original_count = len(search_terms)
            
            for broader_topic in broader_topics:
                broader_topic_lower = broader_topic.lower().strip()
                if broader_topic_lower not in seen and broader_topic_lower:
                    seen.add(broader_topic_lower)
                    search_terms.insert(len(search_terms), broader_topic.strip())
                    broader_topics_added = True
            
            if broader_topics_added:
                logger.info(f"Added {len(search_terms) - original_count} broader topics to search terms")
    
    # Research each search term (articles that don't exist will be skipped automatically)
    wikipedia_results = {}
    successful_searches = 0
    
    logger.info(f"Starting Wikipedia research for {len(search_terms)} search terms")
    
    for i, term in enumerate(search_terms[:5]):  # Limit to first 5 terms to avoid rate limiting
        logger.info(f"Searching Wikipedia for: '{term}' ({i+1}/{min(5, len(search_terms))})")
        
        # Check if we already have this article cached
        safe_title = re.sub(r'[^\w\s-]', '', term).strip()
        safe_title = re.sub(r'[-\s]+', '-', safe_title)
        cached_path = Path("research_sources") / f"{safe_title}.md"
        
        if cached_path.exists():
            logger.info(f"Using cached article for: {term}")
            wikipedia_results[term] = {
                "title": term,
                "url": f"https://en.wikipedia.org/wiki/{term.replace(' ', '_')}",
                "cached": True,
                "status": "found_cached"
            }
            successful_searches += 1
            continue
        
        try:
            result = scraper.search_article(term)
            
            if "error" not in result:
                wikipedia_results[term] = result
                successful_searches += 1
                logger.info(f"Successfully researched: {term}")
            else:
                logger.warning(f"Failed to research '{term}': {result.get('error', 'Unknown error')}")
                wikipedia_results[term] = {"error": result.get('error', 'Search failed')}
                
        except Exception as e:
            logger.error(f"Exception while researching '{term}': {e}")
            wikipedia_results[term] = {"error": f"Exception: {str(e)}"}
    
    return {
        "general_topic": topic,
        "parsed_key_points": parsed_points,
        "search_terms": search_terms,
        "wikipedia_results": wikipedia_results,
        "successful_searches": successful_searches,
        "total_searches": len(search_terms)
    }
