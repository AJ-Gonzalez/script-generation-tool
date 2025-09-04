import os
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import re

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False

logger = logging.getLogger(__name__)


class ChromaStorage:
    
    def __init__(self, folder_path: str, db_path: str = "./chroma_db"):
        self.folder_path = Path(folder_path)
        self.db_path = db_path
        self.collection_name = "document_chunks"
        self.client = None
        self.collection = None
        
        if not CHROMADB_AVAILABLE:
            logger.error("ChromaDB not available - install with: pip install chromadb")
            return
            
        try:
            self.client = chromadb.PersistentClient(path=db_path)
            self._initialize_collection()
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
    
    def _initialize_collection(self):
        try:
            self.collection = self.client.get_collection(self.collection_name)
            logger.info(f"Loaded existing collection: {self.collection_name}")
        except Exception:
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "Document chunks for LLM context"}
            )
            logger.info(f"Created new collection: {self.collection_name}")
    
    def _chunk_markdown(self, content: str, file_path: str) -> List[Dict]:
        chunks = []
        
        # Split by headers and paragraphs
        sections = re.split(r'\n(?=#{1,6}\s)', content)
        
        for i, section in enumerate(sections):
            if not section.strip():
                continue
                
            # Further split large sections by double newlines (paragraphs)
            paragraphs = section.split('\n\n')
            current_chunk = ""
            
            for paragraph in paragraphs:
                if len(current_chunk + paragraph) > 1000:  # Reasonable chunk size
                    if current_chunk:
                        chunks.append({
                            'content': current_chunk.strip(),
                            'source': file_path,
                            'chunk_id': f"{file_path}_{len(chunks)}"
                        })
                    current_chunk = paragraph
                else:
                    current_chunk += "\n\n" + paragraph if current_chunk else paragraph
            
            # Add remaining content
            if current_chunk.strip():
                chunks.append({
                    'content': current_chunk.strip(),
                    'source': file_path,
                    'chunk_id': f"{file_path}_{len(chunks)}"
                })
        
        return chunks
    
    def load_documents(self) -> bool:
        if not self.client or not CHROMADB_AVAILABLE:
            logger.error("ChromaDB not available")
            return False
            
        try:
            # Clear existing collection
            self.client.delete_collection(self.collection_name)
            self._initialize_collection()
            
            all_chunks = []
            
            # Process all markdown files
            for file_path in self.folder_path.rglob("*.md"):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    chunks = self._chunk_markdown(content, str(file_path))
                    all_chunks.extend(chunks)
                    logger.info(f"Processed {file_path}: {len(chunks)} chunks")
                    
                except Exception as e:
                    logger.error(f"Failed to process {file_path}: {e}")
            
            # Add to ChromaDB
            if all_chunks:
                documents = [chunk['content'] for chunk in all_chunks]
                metadatas = [{'source': chunk['source'], 'chunk_id': chunk['chunk_id']} 
                           for chunk in all_chunks]
                ids = [chunk['chunk_id'] for chunk in all_chunks]
                
                self.collection.add(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )
                
                logger.info(f"Loaded {len(all_chunks)} chunks from {len(set(chunk['source'] for chunk in all_chunks))} files")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to load documents: {e}")
            return False
    
    def search(self, query: str, topic_context: str = "", n_results: int = 5) -> List[Dict]:
        if not self.collection or not CHROMADB_AVAILABLE:
            logger.error("ChromaDB not available or collection not initialized")
            return []
        
        try:
            # Combine query with topic context
            search_query = f"{topic_context} {query}".strip()
            
            results = self.collection.query(
                query_texts=[search_query],
                n_results=n_results
            )
            
            formatted_results = []
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    formatted_results.append({
                        'content': doc,
                        'source': results['metadatas'][0][i]['source'],
                        'chunk_id': results['metadatas'][0][i]['chunk_id'],
                        'distance': results['distances'][0][i] if results.get('distances') else None
                    })
            
            logger.info(f"Found {len(formatted_results)} results for query: {query}")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def get_context_for_llm(self, query: str, topic_context: str = "", max_context_length: int = 4000) -> str:
        results = self.search(query, topic_context, n_results=10)
        
        if not results:
            return ""
        
        context_parts = []
        current_length = 0
        
        for result in results:
            content = result['content']
            source = Path(result['source']).name
            
            part = f"Source: {source}\n{content}\n\n"
            
            if current_length + len(part) > max_context_length:
                break
                
            context_parts.append(part)
            current_length += len(part)
        
        return "".join(context_parts).strip()
    
    def get_quick_answer(self, question: str, topic_context: str = "", max_results: int = 3) -> str:
        """
        Get a quick, human-readable answer by combining relevant search results.
        
        Args:
            question: The question to answer
            topic_context: Additional context to improve search
            max_results: Maximum number of search results to combine
            
        Returns:
            Human-readable answer combining relevant information
        """
        results = self.search(question, topic_context, n_results=max_results)
        
        if not results:
            return f"No information found for: {question}"
        
        # Extract and combine meaningful content
        all_content = []
        sources_used = []
        
        for result in results:
            source_name = Path(result['source']).name.replace('.md', '').replace('_', ' ').replace('-', ' ')
            content = result['content'].strip()
            
            # Extract meaningful content from this result
            meaningful_content = self._extract_coherent_content(content, question)
            
            if meaningful_content:
                all_content.append(meaningful_content)
                sources_used.append(source_name)
        
        if not all_content:
            return f"No relevant information found for: {question}"
        
        # Combine into coherent answer
        answer_text = self._combine_content_coherently(all_content, question)
        
        # Format final response
        response_parts = []
        response_parts.append(f"**Question:** {question}\n")
        
        if topic_context:
            response_parts.append(f"**Context:** {topic_context}\n")
        
        response_parts.append("**Answer:**")
        response_parts.append(answer_text)
        
        # Add sources section
        if sources_used:
            unique_sources = list(dict.fromkeys(sources_used))
            response_parts.append(f"\n**Sources:** {', '.join(unique_sources)}")
        
        return '\n'.join(response_parts)
    
    def _extract_coherent_content(self, content: str, question: str) -> str:
        """
        Extract coherent, complete content from a chunk without cutting off mid-sentence.
        
        Args:
            content: Raw content from search result
            question: The original question for relevance scoring
            
        Returns:
            Complete, coherent content related to the question
        """
        # Clean the content first
        content = self._clean_content(content)
        
        # Split into paragraphs first (better than sentences for coherence)
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        
        if not paragraphs:
            return ""
        
        # Score paragraphs by relevance to question
        question_words = set(question.lower().split())
        scored_paragraphs = []
        
        for para in paragraphs:
            # Skip very short paragraphs or markup
            if len(para) < 30 or para.startswith(('#', '*', '-', '|', '[')):
                continue
            
            # Score based on question word overlap
            para_words = set(para.lower().split())
            relevance_score = len(question_words.intersection(para_words))
            
            # Bonus for longer paragraphs (more informative)
            length_score = min(len(para) / 100, 3)  # Cap at 3 bonus points
            
            total_score = relevance_score + length_score
            scored_paragraphs.append((para, total_score))
        
        if not scored_paragraphs:
            return paragraphs[0] if paragraphs else ""
        
        # Sort by score (highest first)
        scored_paragraphs.sort(key=lambda x: -x[1])
        
        # Return the best paragraph, complete
        return scored_paragraphs[0][0]
    
    def _clean_content(self, content: str) -> str:
        """Clean content by removing all Wikipedia and markdown artifacts for readability."""
        
        # Remove Wikipedia-specific artifacts
        content = re.sub(r'\[\[([^\]]+)\|([^\]]+)\]\]', r'\2', content)  # Wiki links with display text
        content = re.sub(r'\[\[([^\]]+)\]\]', r'\1', content)  # Simple wiki links
        content = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', content)  # Markdown links
        content = re.sub(r'{{[^}]+}}', '', content)  # Template calls
        content = re.sub(r'<ref[^>]*>.*?</ref>', '', content, flags=re.DOTALL)  # References
        content = re.sub(r'<ref[^>]*\s*/>', '', content)  # Self-closing refs
        content = re.sub(r'<[^>]+>', '', content)  # HTML tags
        
        # Remove citation artifacts
        content = re.sub(r'\[\d+\]', '', content)  # Citation numbers [1] [2]
        content = re.sub(r'\([^)]*\bcitation needed\b[^)]*\)', '', content, flags=re.IGNORECASE)
        content = re.sub(r'\([^)]*\bwhen\?\b[^)]*\)', '', content, flags=re.IGNORECASE)
        content = re.sub(r'\([^)]*\baccording to whom\?\b[^)]*\)', '', content, flags=re.IGNORECASE)
        
        # Remove markdown formatting
        content = re.sub(r'^#{1,6}\s*', '', content, flags=re.MULTILINE)  # Headers
        content = re.sub(r'^\*+\s*', '', content, flags=re.MULTILINE)  # Bullet points
        content = re.sub(r'^-+\s*', '', content, flags=re.MULTILINE)  # Dashes
        content = re.sub(r'^\|.*\|$', '', content, flags=re.MULTILINE)  # Tables
        content = re.sub(r'\*\*([^*]+)\*\*', r'\1', content)  # Bold
        content = re.sub(r'\*([^*]+)\*', r'\1', content)  # Italic
        content = re.sub(r'`([^`]+)`', r'\1', content)  # Code
        
        # Clean up spacing and empty lines
        content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)  # Multiple empty lines
        content = re.sub(r'[ \t]+', ' ', content)  # Multiple spaces/tabs
        
        # Split into lines and filter out Wikipedia navigation/metadata
        lines = content.split('\n')
        filtered_lines = []
        skip_phrases = [
            'see also', 'external links', 'references', 'further reading', 'categories',
            'bibliography', 'notes', 'sources', 'portal:', 'category:', 'file:',
            'thumb|', 'left|', 'right|', 'center|', 'px|', 'disambiguation',
            'coordinates:', 'wikidata', 'commons category', 'wikimedia',
            'this article', 'main article', 'for other uses', 'redirect',
            'may refer to', 'infobox', 'navbox'
        ]
        
        for line in lines:
            line = line.strip()
            if not line:
                filtered_lines.append('')
                continue
                
            line_lower = line.lower()
            
            # Skip lines that are purely navigation/metadata
            if any(phrase in line_lower for phrase in skip_phrases):
                continue
                
            # Skip lines that look like file/image captions
            if (line_lower.startswith(('thumb|', 'file:', 'image:', '[[file:', '[[image:')) or
                'px|' in line_lower and ('thumb' in line_lower or 'left|' in line_lower)):
                continue
                
            # Skip very short lines that are likely artifacts
            if len(line) < 10 and not line.endswith('.'):
                continue
                
            # Skip lines that are mostly punctuation or numbers
            if len(re.sub(r'[^\w\s]', '', line)) < len(line) * 0.5:
                continue
            
            filtered_lines.append(line)
        
        # Join and final cleanup
        result = '\n'.join(filtered_lines).strip()
        
        # Remove any remaining artifacts
        result = re.sub(r'\s*\([^)]*disambiguation[^)]*\)', '', result, flags=re.IGNORECASE)
        result = re.sub(r'\s*\([^)]*see [^)]*\)', '', result, flags=re.IGNORECASE)
        
        return result
    
    def _combine_content_coherently(self, content_pieces: List[str], question: str) -> str:
        """
        Combine multiple content pieces into a coherent answer.
        
        Args:
            content_pieces: List of relevant content from different sources
            question: Original question for context
            
        Returns:
            Well-formatted, coherent answer
        """
        if not content_pieces:
            return "No relevant information found."
        
        # If we have multiple pieces, present them as a flowing answer
        if len(content_pieces) == 1:
            return content_pieces[0]
        
        # Combine multiple pieces with good transitions
        combined_parts = []
        
        for i, piece in enumerate(content_pieces):
            # First piece gets no prefix
            if i == 0:
                combined_parts.append(piece)
            # Additional pieces get connecting phrases
            elif i == 1:
                combined_parts.append(f"\n\nAdditionally, {piece.lower()[0] + piece[1:] if piece else ''}")
            else:
                combined_parts.append(f"\n\nFurthermore, {piece.lower()[0] + piece[1:] if piece else ''}")
        
        return ''.join(combined_parts)
    
    def is_available(self) -> bool:
        return CHROMADB_AVAILABLE and self.client is not None