"""
 • Main search: Uses Wikipedia REST API to find and
  extract articles
  • Data extraction: Title, URL, summary, key facts 
  with numbers/dates, section headings + content•   
  Related articles: Pulls up to 2 from "See also"        
  sections or article links
  • Edge cases handled:
  - Disambiguation pages → picks most relevant match     
  - Short articles → grabs extra related article
  - No results → returns helpful error message
  • Rate limiting: 1-second delays between API calls     
  (configurable)
  • File saving: Articles saved as Markdown in
  research_sources/ folder
  • Research dossier format: Structured output with      
  Key Facts, Context & Background, Different Angles,     
  Related Topics, and Sources

  Usage:

  scraper = WikipediaScraper(delay=1.0)
  result = scraper.search_article("Climate Change")  
"""

import requests
import time
import logging
import re
import os
from typing import Dict, List, Optional, Union
from urllib.parse import unquote
import markdown2
from pathlib import Path

SOURCES = "research_sources"

logger = logging.getLogger(__name__)


class WikipediaScraper:
    def __init__(self, delay: float = 1.0):
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'WikipediaScraper/1.0 (Educational Research Tool)'
        })

        # Ensure sources directory exists
        Path(SOURCES).mkdir(exist_ok=True)

    def search_article(self, topic: str) -> Dict:
        try:
            # Search for the topic
            search_results = self._search_wikipedia(topic)
            if not search_results:
                return {"error": f"No Wikipedia articles found for '{topic}'"}

            # Get main article
            main_article = self._extract_article_data(search_results[0])
            if not main_article:
                return {"error": f"Failed to extract data for '{topic}'"}

            # Handle disambiguation pages
            if self._is_disambiguation_page(main_article):
                main_article = self._handle_disambiguation(main_article, topic)

            # Get related articles
            related_articles = self._get_related_articles(
                main_article, max_count=2)

            # If main article is too short, get an extra related article
            if len(main_article.get('content', '')) < 1000 and len(related_articles) == 2:
                extra_related = self._get_related_articles(
                    main_article, max_count=3)
                if len(extra_related) > 2:
                    related_articles = extra_related

            # Save articles as files
            self._save_article_files(main_article, related_articles)

            # Structure for research dossier
            return self._format_research_dossier(main_article, related_articles)

        except Exception as e:
            logger.error(f"Error scraping Wikipedia for '{topic}': {str(e)}")
            return {"error": f"Scraping failed: {str(e)}"}

    def _search_wikipedia(self, query: str) -> List[str]:
        time.sleep(self.delay)

        search_url = "https://en.wikipedia.org/w/api.php"
        params = {
            'action': 'opensearch',
            'search': query,
            'limit': 10,
            'format': 'json'
        }

        response = self.session.get(search_url, params=params)
        response.raise_for_status()

        data = response.json()
        # OpenSearch returns [query, titles, descriptions, urls]
        if len(data) >= 2:
            return data[1]  # Return titles
        return []

    def _extract_article_data(self, title: str) -> Optional[Dict]:
        time.sleep(self.delay)

        # Get page content using standard Wikipedia API
        api_url = "https://en.wikipedia.org/w/api.php"
        
        # Get page extract/summary
        extract_params = {
            'action': 'query',
            'format': 'json',
            'titles': title,
            'prop': 'extracts|info',
            'exintro': True,
            'explaintext': True,
            'inprop': 'url'
        }
        
        extract_response = self.session.get(api_url, params=extract_params)
        extract_response.raise_for_status()
        extract_data = extract_response.json()
        
        pages = extract_data.get('query', {}).get('pages', {})
        if not pages:
            return None
            
        page_data = next(iter(pages.values()))
        if page_data.get('missing'):
            return None

        # Get full page content in HTML
        content_params = {
            'action': 'parse',
            'format': 'json',
            'page': title,
            'prop': 'text'
        }
        
        content_response = self.session.get(api_url, params=content_params)
        content_response.raise_for_status()
        content_data = content_response.json()
        
        html_content = content_data.get('parse', {}).get('text', {}).get('*', '')

        return {
            'title': page_data.get('title', title),
            'url': page_data.get('fullurl', f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}"),
            'summary': page_data.get('extract', ''),
            'html_content': html_content,
            'page_key': title
        }

    def _is_disambiguation_page(self, article: Dict) -> bool:
        return 'disambiguation' in article.get('title', '').lower() or \
               'may refer to' in article.get('summary', '').lower()

    def _handle_disambiguation(self, article: Dict, original_topic: str) -> Dict:
        # Extract links from disambiguation page
        html_content = article.get('html_content', '')

        # Look for the most relevant link based on original topic
        links = re.findall(
            r'<a href="/wiki/([^"]+)"[^>]*>([^<]+)</a>', html_content)

        best_match = None
        best_score = 0

        for link, text in links[:10]:  # Check first 10 links
            score = self._calculate_relevance_score(text, original_topic)
            if score > best_score:
                best_score = score
                best_match = unquote(link)

        if best_match:
            return self._extract_article_data(best_match.replace('_', ' '))

        return article

    def _calculate_relevance_score(self, text: str, topic: str) -> float:
        text_lower = text.lower()
        topic_lower = topic.lower()

        score = 0
        topic_words = topic_lower.split()

        for word in topic_words:
            if word in text_lower:
                score += 1

        return score / len(topic_words) if topic_words else 0

    def _get_related_articles(self, article: Dict, max_count: int = 2) -> List[Dict]:
        html_content = article.get('html_content', '')
        related_articles = []

        # Extract "See also" section links
        see_also_pattern = r'<h2[^>]*>See also</h2>.*?(?=<h2|$)'
        see_also_match = re.search(
            see_also_pattern, html_content, re.DOTALL | re.IGNORECASE)

        if see_also_match:
            see_also_content = see_also_match.group()
            links = re.findall(
                r'<a href="/wiki/([^"]+)"[^>]*>([^<]+)</a>', see_also_content)

            for link, _ in links[:max_count]:
                try:
                    title = unquote(link).replace('_', ' ')
                    related_data = self._extract_article_data(title)
                    if related_data:
                        related_articles.append(related_data)
                except:
                    continue

        # If not enough from "See also", get from regular links
        if len(related_articles) < max_count:
            all_links = re.findall(
                r'<a href="/wiki/([^"]+)"[^>]*>([^<]+)</a>', html_content)

            for link, _ in all_links[:20]:  # Check first 20 links
                if len(related_articles) >= max_count:
                    break

                try:
                    link_decoded = unquote(link)
                    # Skip common Wikipedia pages and portal pages
                    if any(skip in link_decoded.lower() for skip in ['category:', 'file:', 'template:', 'help:', 'portal:']):
                        continue

                    title = link_decoded.replace('_', ' ')
                    related_data = self._extract_article_data(title)
                    if related_data and related_data not in related_articles:
                        related_articles.append(related_data)
                except:
                    continue

        return related_articles[:max_count]

    def _save_article_files(self, main_article: Dict, related_articles: List[Dict]):
        # Save main article
        self._save_single_article(main_article, is_main=True)

        # Save related articles
        for i, article in enumerate(related_articles):
            self._save_single_article(
                article, is_main=False, suffix=f"_related_{i+1}")

    def _save_single_article(self, article: Dict, is_main: bool = True, suffix: str = ""):
        if not article:
            return

        title = article.get('title', 'Unknown')
        safe_title = re.sub(r'[^\w\s-]', '', title).strip()
        safe_title = re.sub(r'[-\s]+', '-', safe_title)

        filename = f"{safe_title}{suffix}"
        md_path = Path(SOURCES) / f"{filename}.md"
        
        # Check if file already exists to save time
        if md_path.exists():
            logger.info(f"Article already exists, skipping: {md_path}")
            return

        # Save as Markdown
        md_content = f"# {title}\n\n"
        md_content += f"**URL:** {article.get('url', '')}\n\n"
        md_content += f"## Summary\n\n{article.get('summary', '')}\n\n"

        # Convert HTML to markdown (simplified)
        html_content = article.get('html_content', '')
        # Basic HTML to markdown conversion
        md_content += self._html_to_markdown(html_content)
        
        # Save new file
        try:
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(md_content)
            logger.info(f"Article saved: {md_path}")
        except Exception as e:
            logger.error(f"Failed to save article to {md_path}: {e}")

    def _html_to_markdown(self, html: str) -> str:
        # Basic HTML to markdown conversion
        # Remove script and style tags
        html = re.sub(
            r'<(script|style)[^>]*>.*?</\1>', '', html, flags=re.DOTALL)

        # Convert headers
        html = re.sub(r'<h([1-6])[^>]*>(.*?)</h\1>', lambda m: '#' *
                      int(m.group(1)) + ' ' + m.group(2) + '\n\n', html)

        # Convert paragraphs
        html = re.sub(r'<p[^>]*>(.*?)</p>', r'\1\n\n', html, flags=re.DOTALL)

        # Remove remaining tags
        html = re.sub(r'<[^>]+>', '', html)

        # Clean up whitespace
        html = re.sub(r'\n\s*\n', '\n\n', html)

        return html.strip()

    def _format_research_dossier(self, main_article: Dict, related_articles: List[Dict]) -> Dict:
        # Extract key facts with numbers/dates
        key_facts = self._extract_key_facts(main_article)

        # Extract main sections
        sections = self._extract_sections(main_article)

        # Create research dossier format
        return {
            "title": main_article.get('title', ''),
            "url": main_article.get('url', ''),
            "key_facts": key_facts,
            "context_background": main_article.get('summary', ''),
            "different_angles": sections,
            "related_topics": [
                {
                    "title": article.get('title', ''),
                    "url": article.get('url', ''),
                    "summary": article.get('summary', '')
                }
                for article in related_articles
            ],
            "sources": [
                main_article.get('url', '')
            ] + [article.get('url', '') for article in related_articles]
        }

    def _extract_key_facts(self, article: Dict) -> List[str]:
        # Clean HTML content first
        html_content = article.get('html_content', '')
        clean_content = self._html_to_text(html_content)
        summary = article.get('summary', '')
        
        facts = []
        
        # Extract key sentences from summary first (usually high quality)
        summary_facts = self._extract_facts_from_summary(summary)
        facts.extend(summary_facts[:3])
        
        # Then look for specific patterns in content
        content = clean_content + ' ' + summary

        # Find dates with better patterns
        date_patterns = [
            r'[^.!?]*(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}[^.!?]*[.!?]',
            r'[^.!?]*\b\d{4}\b[^.!?]*(?:launched|founded|established|built|created|invented)[^.!?]*[.!?]',
            r'[^.!?]*(?:launched|founded|established|built|created|invented)[^.!?]*\b\d{4}\b[^.!?]*[.!?]'
        ]

        # Find numbers with meaningful context
        number_patterns = [
            r'[^.!?]*\d+(?:,\d{3})*(?:\.\d+)?\s*(?:million|billion|thousand|percent|%)[^.!?]*[.!?]',
            r'[^.!?]*\$\d+(?:,\d{3})*(?:\.\d+)?(?:\s*(?:million|billion|thousand))?[^.!?]*[.!?]',
            r'[^.!?]*\d+(?:,\d{3})*\s*(?:km|miles|feet|meters|years|people|users|countries|planets|galaxies)[^.!?]*[.!?]'
        ]

        all_patterns = date_patterns + number_patterns

        for pattern in all_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
            for match in matches[:2]:  # Limit to 2 per pattern
                clean_match = match.strip()
                # Only add if it's substantial and not a duplicate
                if (len(clean_match) > 30 and 
                    clean_match not in facts and 
                    not any(self._facts_overlap(clean_match, f) for f in facts)):
                    facts.append(clean_match)

        return facts[:6]  # Limit to 6 key facts
    
    def _extract_facts_from_summary(self, summary: str) -> List[str]:
        """Extract key facts from the summary"""
        if not summary:
            return []
        
        # Split into sentences
        sentences = re.split(r'[.!?]+', summary)
        facts = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 30:  # Skip short sentences
                continue
                
            # Look for sentences with numbers, dates, or significant keywords
            has_number = re.search(r'\d+(?:,\d{3})*(?:\.\d+)?', sentence)
            has_date = re.search(r'\b\d{4}\b|January|February|March|April|May|June|July|August|September|October|November|December', sentence)
            has_significance = any(word in sentence.lower() for word in [
                'first', 'largest', 'founded', 'established', 'launched', 'invented', 
                'created', 'became', 'achieved', 'million', 'billion', 'percent'
            ])
            
            if has_number or has_date or has_significance:
                facts.append(sentence + '.')
        
        return facts[:3]
    
    def _facts_overlap(self, fact1: str, fact2: str) -> bool:
        """Check if two facts overlap significantly"""
        words1 = set(fact1.lower().split())
        words2 = set(fact2.lower().split())
        
        # Remove common words
        common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        words1 -= common_words
        words2 -= common_words
        
        if len(words1) == 0 or len(words2) == 0:
            return False
        
        overlap = len(words1 & words2) / min(len(words1), len(words2))
        return overlap > 0.6
    
    def _html_to_text(self, html: str) -> str:
        """Convert HTML to clean text"""
        if not html:
            return ""
        
        # Remove script and style tags
        html = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', html, flags=re.DOTALL)
        
        # Remove citations and references
        html = re.sub(r'<sup[^>]*>.*?</sup>', '', html, flags=re.DOTALL)
        
        # Convert line breaks
        html = re.sub(r'<br[^>]*>', ' ', html)
        
        # Remove all remaining tags
        html = re.sub(r'<[^>]+>', '', html)
        
        # Clean up whitespace and decode HTML entities
        html = re.sub(r'\s+', ' ', html)
        html = html.replace('&nbsp;', ' ')
        html = html.replace('&amp;', '&')
        html = html.replace('&lt;', '<')
        html = html.replace('&gt;', '>')
        html = html.replace('&quot;', '"')
        html = html.replace('&#39;', "'")
        
        return html.strip()

    def _extract_sections(self, article: Dict) -> List[Dict]:
        html_content = article.get('html_content', '')

        sections = []

        # Find h2 sections
        section_pattern = r'<h2[^>]*>(.*?)</h2>(.*?)(?=<h2|$)'
        section_matches = re.findall(section_pattern, html_content, re.DOTALL)

        for heading, content in section_matches[:5]:  # Limit to 5 sections
            # Clean heading
            heading_clean = re.sub(r'<[^>]+>', '', heading).strip()

            # Clean content and get first paragraph
            content_clean = re.sub(r'<[^>]+>', '', content)
            content_clean = re.sub(r'\s+', ' ', content_clean).strip()

            if heading_clean and content_clean:
                sections.append({
                    "heading": heading_clean,
                    "content": content_clean[:500] + "..." if len(content_clean) > 500 else content_clean
                })

        return sections
    
    def generate_markdown_dossier(self, topic: str) -> str:
        """Generate a human-readable markdown dossier with images"""
        # Get the research data
        data = self.search_article(topic)
        
        if "error" in data:
            return f"# Research Dossier Error\n\n{data['error']}"
        
        # Extract images from main article
        images = self._extract_images(data.get('title', ''))
        
        # Build markdown dossier
        md_content = f"# Research Dossier: {data['title']}\n\n"
        
        # Add main image if available
        if images:
            md_content += f"![{data['title']}]({images[0]['url']})\n"
            md_content += f"*{images[0].get('description', data['title'])}*\n\n"
        
        md_content += f"**Source:** [{data['title']}]({data['url']})\n\n"
        md_content += "---\n\n"
        
        # Context & Background
        md_content += "## Executive Summary\n\n"
        md_content += f"{data['context_background']}\n\n"
        
        # Key Facts
        if data.get('key_facts'):
            md_content += "## Key Facts & Figures\n\n"
            for fact in data['key_facts']:
                # Clean up the fact and make it more presentable
                clean_fact = self._clean_fact_for_display(fact)
                if clean_fact:  # Only add if fact is meaningful
                    md_content += f"• {clean_fact}\n"
            md_content += "\n"
        
        # Different Angles/Sections
        if data.get('different_angles'):
            md_content += "## Detailed Analysis\n\n"
            for section in data['different_angles'][:4]:  # Limit to 4 sections
                md_content += f"### {section['heading']}\n\n"
                md_content += f"{section['content']}\n\n"
        
        # Additional Images
        if len(images) > 1:
            md_content += "## Visual References\n\n"
            for img in images[1:3]:  # Show 2 additional images
                md_content += f"![{img.get('description', 'Image')}]({img['url']})\n"
                if img.get('description'):
                    md_content += f"*{img['description']}*\n\n"
        
        # Related Topics
        if data.get('related_topics'):
            md_content += "## Related Research Areas\n\n"
            for topic in data['related_topics']:
                md_content += f"### [{topic['title']}]({topic['url']})\n"
                if topic.get('summary'):
                    md_content += f"{topic['summary'][:200]}...\n\n"
        
        # Sources
        md_content += "## Sources & References\n\n"
        for i, source in enumerate(data['sources'], 1):
            md_content += f"{i}. [{source}]({source})\n"
        
        md_content += f"\n---\n*Generated on {time.strftime('%B %d, %Y')} using WikipediaScraper*\n"
        
        # Save the dossier to SOURCES directory
        self._save_dossier_to_sources(topic, md_content)
        
        return md_content
    
    def _save_dossier_to_sources(self, topic: str, md_content: str):
        """Save the markdown dossier to SOURCES directory"""
        # Create safe filename from topic
        safe_topic = re.sub(r'[^\w\s-]', '', topic).strip()
        safe_topic = re.sub(r'[-\s]+', '-', safe_topic)
        
        dossier_filename = f"dossier-{safe_topic}.md"
        dossier_path = Path(SOURCES) / dossier_filename
        
        # Check if dossier already exists to save time
        if dossier_path.exists():
            logger.info(f"Dossier already exists, skipping: {dossier_path}")
            return
        
        try:
            # Save new dossier
            with open(dossier_path, 'w', encoding='utf-8') as f:
                f.write(md_content)
            logger.info(f"Dossier saved: {dossier_path}")
        except Exception as e:
            logger.error(f"Failed to save dossier to {dossier_path}: {e}")
    
    def _extract_images(self, title: str) -> List[Dict]:
        """Extract images from Wikipedia article"""
        time.sleep(self.delay)
        
        api_url = "https://en.wikipedia.org/w/api.php"
        
        # Get images from the article
        params = {
            'action': 'query',
            'format': 'json',
            'titles': title,
            'prop': 'images',
            'imlimit': 10
        }
        
        try:
            response = self.session.get(api_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            pages = data.get('query', {}).get('pages', {})
            if not pages:
                return []
            
            page_data = next(iter(pages.values()))
            images_list = page_data.get('images', [])
            
            # Get image info for each image
            processed_images = []
            for img_data in images_list[:5]:  # Limit to 5 images
                img_title = img_data.get('title', '')
                
                # Skip common non-content images
                if any(skip in img_title.lower() for skip in ['commons-logo', 'edit-icon', 'wikimedia', 'disambiguation']):
                    continue
                
                # Get image URL and info
                img_info = self._get_image_info(img_title)
                if img_info:
                    processed_images.append(img_info)
            
            return processed_images
            
        except Exception as e:
            logger.error(f"Error extracting images: {str(e)}")
            return []
    
    def _get_image_info(self, image_title: str) -> Optional[Dict]:
        """Get image URL and description"""
        time.sleep(0.5)  # Shorter delay for image requests
        
        api_url = "https://en.wikipedia.org/w/api.php"
        
        params = {
            'action': 'query',
            'format': 'json',
            'titles': image_title,
            'prop': 'imageinfo',
            'iiprop': 'url|extmetadata',
            'iiurlwidth': 800  # Get medium-sized image
        }
        
        try:
            response = self.session.get(api_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            pages = data.get('query', {}).get('pages', {})
            if not pages:
                return None
            
            page_data = next(iter(pages.values()))
            imageinfo = page_data.get('imageinfo', [])
            
            if imageinfo:
                img_info = imageinfo[0]
                result = {
                    'url': img_info.get('thumburl', img_info.get('url', '')),
                    'title': image_title,
                    'description': ''
                }
                
                # Extract description from metadata
                extmetadata = img_info.get('extmetadata', {})
                if 'ImageDescription' in extmetadata:
                    desc = extmetadata['ImageDescription'].get('value', '')
                    # Clean HTML from description
                    desc = re.sub(r'<[^>]+>', '', desc)
                    result['description'] = desc[:200] + "..." if len(desc) > 200 else desc
                
                return result
            
        except Exception as e:
            logger.error(f"Error getting image info for {image_title}: {str(e)}")
            return None
    
    def _clean_fact_for_display(self, fact: str) -> str:
        """Clean and format a fact for better display"""
        if not fact or len(fact) < 10:
            return ""
        
        # Remove fragments and incomplete sentences
        fact = fact.strip()
        
        # Skip facts that are clearly fragments (start with lowercase, weird punctuation)
        if fact[0].islower() or fact.startswith(('^', '[', ']', '?', '&')):
            return ""
        
        # Skip facts that are mostly references or citations
        if fact.count('^') > 2 or fact.count('[') > 2 or len(fact) < 20:
            return ""
        
        # Clean up common artifacts
        fact = re.sub(r'\[\d+\]', '', fact)  # Remove citation numbers
        fact = re.sub(r'\^[^.]*\^', '', fact)  # Remove reference markers
        fact = re.sub(r'Retrieved \d+.*?\d+\.', '', fact)  # Remove "Retrieved" dates
        fact = re.sub(r'Archived from.*?on.*?\d+\.', '', fact)  # Remove archive info
        fact = re.sub(r'\s+', ' ', fact)  # Normalize whitespace
        
        # Ensure it ends properly
        if not fact.endswith(('.', '!', '?', '%')):
            # Try to find a natural ending point
            sentences = re.split(r'[.!?]', fact)
            if len(sentences) > 1 and len(sentences[0]) > 20:
                fact = sentences[0] + '.'
        
        # Final cleanup
        fact = fact.strip()
        
        # Skip if too short or still looks like a fragment
        if len(fact) < 25 or not fact[0].isupper():
            return ""
        
        return fact
