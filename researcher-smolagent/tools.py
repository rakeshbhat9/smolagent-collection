"""
Research tools for the multi-agent research system.

Provides 5 core tools:
1. web_search - Search the web using DuckDuckGo
2. scrape_webpage - Extract content from webpages
3. analyze_document - Analyze PDFs and documents
4. synthesize_data - Aggregate information from multiple sources
5. track_citations - Extract and manage citations
"""

import os
import re
import json
import hashlib
import time
from datetime import datetime
from typing import List, Dict
from smolagents import tool
import requests
from bs4 import BeautifulSoup

# Cache directory
CACHE_DIR = os.getenv("CACHE_DIR", "data/research_cache")
os.makedirs(CACHE_DIR, exist_ok=True)


def _get_cache_path(key: str) -> str:
    """Generate cache file path from key."""
    hashed = hashlib.md5(key.encode()).hexdigest()
    return os.path.join(CACHE_DIR, f"{hashed}.json")


def _load_from_cache(key: str, max_age_hours: int = 24) -> dict:
    """Load data from cache if available and fresh."""
    cache_path = _get_cache_path(key)
    if os.path.exists(cache_path):
        try:
            with open(cache_path, 'r') as f:
                cached = json.load(f)
                cache_time = datetime.fromisoformat(cached.get('timestamp', ''))
                age_hours = (datetime.now() - cache_time).total_seconds() / 3600
                if age_hours < max_age_hours:
                    return cached.get('data')
        except (json.JSONDecodeError, ValueError):
            pass
    return None


def _save_to_cache(key: str, data: dict):
    """Save data to cache."""
    cache_path = _get_cache_path(key)
    try:
        with open(cache_path, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'data': data
            }, f)
    except Exception as e:
        print(f"Cache save failed: {e}")


@tool
def web_search(query: str, max_results: int = 5) -> dict:
    """
    Search the web for information using DuckDuckGo.

    Args:
        query: The search query to execute
        max_results: Maximum number of results to return (default: 5)

    Returns:
        dict: {
            "query": str,
            "results": [
                {
                    "title": str,
                    "url": str,
                    "snippet": str,
                    "source": str
                }
            ],
            "total_results": int
        }
    """
    try:
        # Check cache first
        cache_key = f"search_{query}_{max_results}"
        cached = _load_from_cache(cache_key, max_age_hours=24)
        if cached:
            return cached

        # Import here to avoid dependency issues if not installed
        from duckduckgo_search import DDGS

        results = []
        with DDGS() as ddgs:
            search_results = ddgs.text(query, max_results=max_results)
            for result in search_results:
                results.append({
                    "title": result.get("title", ""),
                    "url": result.get("href", ""),
                    "snippet": result.get("body", ""),
                    "source": result.get("href", "").split("/")[2] if "/" in result.get("href", "") else "unknown"
                })

        response = {
            "query": query,
            "results": results,
            "total_results": len(results)
        }

        # Cache the results
        _save_to_cache(cache_key, response)

        return response

    except Exception as e:
        return {
            "error": str(e),
            "query": query,
            "results": [],
            "total_results": 0
        }


@tool
def scrape_webpage(url: str, extract_links: bool = False) -> dict:
    """
    Scrape and extract content from a webpage.

    Args:
        url: The URL to scrape
        extract_links: Whether to extract links from the page

    Returns:
        dict: {
            "url": str,
            "title": str,
            "content": str,
            "metadata": {
                "author": str or None,
                "publish_date": str or None,
                "word_count": int
            },
            "links": [str] if extract_links else []
        }
    """
    try:
        # Check cache
        cache_key = f"scrape_{url}"
        cached = _load_from_cache(cache_key, max_age_hours=168)  # 7 days
        if cached:
            return cached

        # Rate limiting
        time.sleep(1)

        # Fetch the page
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        # Parse with BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')

        # Extract title
        title = soup.find('title').get_text() if soup.find('title') else "No title"

        # Try to use newspaper3k for better extraction
        try:
            from newspaper import Article
            article = Article(url)
            article.set_html(response.content)
            article.parse()
            content = article.text
            author = ', '.join(article.authors) if article.authors else None
            publish_date = article.publish_date.isoformat() if article.publish_date else None
        except:
            # Fallback to basic extraction
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "aside"]):
                script.decompose()

            # Get text
            content = soup.get_text()
            # Clean up whitespace
            lines = (line.strip() for line in content.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            content = '\n'.join(chunk for chunk in chunks if chunk)

            author = None
            publish_date = None

        # Extract links if requested
        links = []
        if extract_links:
            for link in soup.find_all('a', href=True):
                href = link['href']
                if href.startswith('http'):
                    links.append(href)

        # Build response
        result = {
            "url": url,
            "title": title,
            "content": content[:10000],  # Limit to first 10k chars
            "metadata": {
                "author": author,
                "publish_date": publish_date,
                "word_count": len(content.split())
            },
            "links": links[:20] if extract_links else []  # Limit to 20 links
        }

        # Cache the result
        _save_to_cache(cache_key, result)

        return result

    except Exception as e:
        return {
            "error": str(e),
            "url": url,
            "title": "",
            "content": "",
            "metadata": {},
            "links": []
        }


@tool
def analyze_document(file_path: str, analysis_type: str = "summary") -> dict:
    """
    Analyze documents (PDF, TXT, DOCX) for research purposes.

    Args:
        file_path: Path to document file or URL to PDF
        analysis_type: Type of analysis - "summary", "extract_citations",
                       "key_points", "full_text"

    Returns:
        dict: {
            "file_path": str,
            "document_type": str,
            "analysis_type": str,
            "content": str,
            "metadata": {
                "page_count": int or None,
                "author": str or None,
                "title": str or None,
                "citations_found": int
            }
        }
    """
    try:
        # Determine if it's a URL or file path
        if file_path.startswith('http'):
            # Download PDF from URL
            response = requests.get(file_path, timeout=30)
            content_bytes = response.content
            doc_type = "pdf"
        else:
            # Read local file
            with open(file_path, 'rb') as f:
                content_bytes = f.read()
            doc_type = file_path.split('.')[-1].lower()

        # Process based on document type
        if doc_type == 'pdf':
            import PyPDF2
            import io

            pdf_reader = PyPDF2.PdfReader(io.BytesIO(content_bytes))
            page_count = len(pdf_reader.pages)

            # Extract text from all pages
            full_text = ""
            for page in pdf_reader.pages:
                full_text += page.extract_text() + "\n"

            # Extract metadata
            metadata = pdf_reader.metadata
            author = metadata.get('/Author', None) if metadata else None
            title = metadata.get('/Title', None) if metadata else None

        elif doc_type in ['txt', 'text']:
            full_text = content_bytes.decode('utf-8')
            page_count = None
            author = None
            title = None

        elif doc_type in ['doc', 'docx']:
            from docx import Document
            import io

            doc = Document(io.BytesIO(content_bytes))
            full_text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            page_count = None
            author = doc.core_properties.author if hasattr(doc, 'core_properties') else None
            title = doc.core_properties.title if hasattr(doc, 'core_properties') else None

        else:
            return {
                "error": f"Unsupported document type: {doc_type}",
                "file_path": file_path,
                "document_type": doc_type,
                "analysis_type": analysis_type,
                "content": "",
                "metadata": {}
            }

        # Perform requested analysis
        if analysis_type == "full_text":
            content = full_text
        elif analysis_type == "summary":
            # Simple summary: first 500 and last 200 words
            words = full_text.split()
            if len(words) > 700:
                content = ' '.join(words[:500]) + "\n\n[...]\n\n" + ' '.join(words[-200:])
            else:
                content = full_text
        elif analysis_type == "extract_citations":
            # Extract text that looks like citations
            citation_patterns = [
                r'\([A-Z][a-z]+(?:,?\s+[A-Z][a-z]+)*,?\s+\d{4}\)',  # (Author, Year)
                r'\[[0-9]+\]',  # [1]
                r'[A-Z][a-z]+\s+et\s+al\.\s+\(\d{4}\)'  # Author et al. (Year)
            ]
            citations = []
            for pattern in citation_patterns:
                citations.extend(re.findall(pattern, full_text))
            content = "\n".join(set(citations))  # Remove duplicates
        elif analysis_type == "key_points":
            # Extract sentences that seem important (containing keywords)
            keywords = ['important', 'significant', 'concluded', 'found', 'demonstrated',
                       'results', 'showed', 'indicates', 'suggests']
            sentences = re.split(r'[.!?]+', full_text)
            key_sentences = [s.strip() for s in sentences
                           if any(kw in s.lower() for kw in keywords)]
            content = "\n\n".join(key_sentences[:10])  # Top 10 key sentences
        else:
            content = full_text[:2000]  # Default: first 2000 chars

        # Count citations
        citation_count = len(re.findall(r'\([A-Z][a-z]+.*?\d{4}\)', full_text))

        return {
            "file_path": file_path,
            "document_type": doc_type,
            "analysis_type": analysis_type,
            "content": content[:15000],  # Limit to 15k chars
            "metadata": {
                "page_count": page_count,
                "author": author,
                "title": title,
                "citations_found": citation_count
            }
        }

    except Exception as e:
        return {
            "error": str(e),
            "file_path": file_path,
            "document_type": "unknown",
            "analysis_type": analysis_type,
            "content": "",
            "metadata": {}
        }


@tool
def synthesize_data(sources: list, synthesis_type: str = "comparison") -> dict:
    """
    Synthesize information from multiple sources.

    Args:
        sources: List of source dictionaries with 'content' and 'source' keys
        synthesis_type: "comparison", "timeline", "consensus", "conflicts"

    Returns:
        dict: {
            "synthesis_type": str,
            "sources_analyzed": int,
            "synthesis": str,
            "key_themes": [str],
            "confidence_level": str
        }
    """
    try:
        if not sources or not isinstance(sources, list):
            return {
                "error": "Sources must be a non-empty list",
                "synthesis_type": synthesis_type,
                "sources_analyzed": 0,
                "synthesis": "",
                "key_themes": [],
                "confidence_level": "low"
            }

        num_sources = len(sources)

        # Extract all content
        all_content = []
        for source in sources:
            if isinstance(source, dict) and 'content' in source:
                all_content.append(source['content'])
            elif isinstance(source, str):
                all_content.append(source)

        combined_text = " ".join(all_content)

        # Simple keyword extraction for themes
        words = re.findall(r'\b[a-z]{4,}\b', combined_text.lower())
        word_freq = {}
        for word in words:
            if word not in ['that', 'this', 'with', 'from', 'have', 'been', 'were', 'their', 'which']:
                word_freq[word] = word_freq.get(word, 0) + 1

        # Top themes
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        key_themes = [word for word, count in sorted_words[:5]]

        # Generate synthesis based on type
        if synthesis_type == "comparison":
            synthesis = f"Analyzed {num_sources} sources. "
            synthesis += f"Common themes include: {', '.join(key_themes)}. "
            synthesis += f"Sources provide varying perspectives on the topic."

        elif synthesis_type == "timeline":
            synthesis = f"Chronological synthesis of {num_sources} sources. "
            synthesis += "Key developments and events documented across sources."

        elif synthesis_type == "consensus":
            synthesis = f"Consensus analysis across {num_sources} sources. "
            synthesis += f"Agreement on key points: {', '.join(key_themes)}."

        elif synthesis_type == "conflicts":
            synthesis = f"Conflict analysis across {num_sources} sources. "
            synthesis += "Identified areas of disagreement and conflicting perspectives."

        else:
            synthesis = f"General synthesis of {num_sources} sources."

        # Confidence based on number of sources
        if num_sources >= 5:
            confidence = "high"
        elif num_sources >= 3:
            confidence = "medium"
        else:
            confidence = "low"

        return {
            "synthesis_type": synthesis_type,
            "sources_analyzed": num_sources,
            "synthesis": synthesis,
            "key_themes": key_themes,
            "confidence_level": confidence
        }

    except Exception as e:
        return {
            "error": str(e),
            "synthesis_type": synthesis_type,
            "sources_analyzed": 0,
            "synthesis": "",
            "key_themes": [],
            "confidence_level": "low"
        }


@tool
def track_citations(content: str, source_url: str = None) -> dict:
    """
    Extract and track citations from research content.

    Args:
        content: Text content to extract citations from
        source_url: Original source URL for attribution

    Returns:
        dict: {
            "citations_found": int,
            "citations": [
                {
                    "citation_text": str,
                    "type": str,
                    "authors": [str],
                    "year": int or None,
                    "source_url": str or None
                }
            ],
            "source_attribution": {
                "url": str or None,
                "credibility_score": float
            }
        }
    """
    try:
        citations = []

        # Pattern 1: (Author, Year) or (Author et al., Year)
        pattern1 = r'\(([A-Z][a-z]+(?:\s+et\s+al\.)?),?\s+(\d{4})\)'
        matches1 = re.findall(pattern1, content)
        for author, year in matches1:
            citations.append({
                "citation_text": f"({author}, {year})",
                "type": "in-text",
                "authors": [author.replace(' et al.', '')],
                "year": int(year),
                "source_url": source_url
            })

        # Pattern 2: [1], [2], etc.
        pattern2 = r'\[(\d+)\]'
        matches2 = re.findall(pattern2, content)
        for num in matches2:
            citations.append({
                "citation_text": f"[{num}]",
                "type": "numbered",
                "authors": [],
                "year": None,
                "source_url": source_url
            })

        # Pattern 3: Author et al. (Year)
        pattern3 = r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+et\s+al\.\s+\((\d{4})\)'
        matches3 = re.findall(pattern3, content)
        for author, year in matches3:
            citations.append({
                "citation_text": f"{author} et al. ({year})",
                "type": "in-text",
                "authors": [author],
                "year": int(year),
                "source_url": source_url
            })

        # Calculate source credibility based on domain
        credibility_score = 0.5  # Default
        if source_url:
            if any(domain in source_url for domain in ['.edu', '.gov', '.ac.uk']):
                credibility_score = 0.9
            elif any(domain in source_url for domain in ['.org', 'arxiv.org', 'doi.org']):
                credibility_score = 0.8
            elif any(domain in source_url for domain in ['nytimes.com', 'bbc.com', 'nature.com', 'science.org']):
                credibility_score = 0.7

        return {
            "citations_found": len(citations),
            "citations": citations,
            "source_attribution": {
                "url": source_url,
                "credibility_score": credibility_score
            }
        }

    except Exception as e:
        return {
            "error": str(e),
            "citations_found": 0,
            "citations": [],
            "source_attribution": {
                "url": source_url,
                "credibility_score": 0.0
            }
        }
