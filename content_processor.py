import re
import logging
import unicodedata
from typing import List, Optional
from bs4 import BeautifulSoup, Tag
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class AdvancedContentProcessor:
    def __init__(self, similarity_threshold: float = 0.7):
        self.similarity_threshold = similarity_threshold
        self.vectorizer = TfidfVectorizer(stop_words='english')
        self.processed_contents: List[str] = []
        self.processed_vectors = None
        
        # Define lists for filtering
        self.boilerplate_selectors = [
            'nav', 'header', 'footer', 'sidebar', 
            '.advertisement', '.ads', '#ads', 
            '.related-content', '.comments'
        ]
        
        self.ad_keywords = [
            'advertisement', 'sponsored', 'related links', 
            'click here', 'view more', 'recommended'
        ]

    def extract_main_content(self, html_content: str) -> str:
        """
        Intelligent main content extraction strategy
        
        Key Steps:
        1. Parse HTML with BeautifulSoup
        2. Remove unnecessary elements
        3. Find the most content-rich container
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script, style, navigation elements
        for element in soup(["script", "style", "nav"] + 
                            [sel for sel in self.boilerplate_selectors]):
            element.decompose()
        
        # Content extraction strategies
        content_strategies = [
            soup.find('article'),
            soup.select_one('.main-content'),
            soup.select_one('#main-content'),
            soup.select_one('.content'),
            soup.body
        ]
        
        for strategy in content_strategies:
            if strategy and isinstance(strategy, Tag):
                text = strategy.get_text(separator=' ', strip=True)
                if self.is_quality_content(text):
                    return text
        
        return ""

    def is_quality_content(self, text: str) -> bool:
        """
        Comprehensive content quality assessment
        
        Evaluation Criteria:
        - Minimum meaningful word count
        - Malayalam character proportion
        - Low advertisement keyword density
        """
        if not text:
            return False
        
        # Malayalam character ratio
        malayalam_chars = sum(1 for char in text if '\u0D00' <= char <= '\u0D7F')
        malayalam_ratio = malayalam_chars / len(text) if text else 0
        
        # Word count and complexity
        words = text.split()
        ad_score = sum(keyword in text.lower() for keyword in self.ad_keywords)
        
        quality_conditions = [
            len(words) > 50,     # Substantial content
            malayalam_ratio > 0.6,  # Predominantly Malayalam
            ad_score < 2            # Minimal advertisement indicators
        ]
        
        return all(quality_conditions)

    def clean_markdown(self, content: str) -> str:
        """
        Advanced markdown cleaning
        
        Removes:
        - Markdown syntax
        - Excessive whitespaces
        - Potential boilerplate content
        """
        # Remove markdown-specific syntax
        content = re.sub(r'#+\s*', '', content)  # Headers
        content = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', content)  # Links
        content = re.sub(r'`{1,3}[^`\n]+`{1,3}', '', content)  # Code blocks
        
        # Normalize Malayalam text
        content = unicodedata.normalize('NFC', content)
        
        # Remove extra whitespaces
        content = re.sub(r'\s+', ' ', content).strip()
        
        return content

    def process_webpage_content(self, url: str, raw_content: str) -> Optional[str]:
        """
        Comprehensive content processing pipeline
        
        Stages:
        1. Encoding handling
        2. Main content extraction
        3. Markdown cleaning
        4. Quality assessment
        """
        try:
            # 1. Handle potential encoding issues
            content = self._handle_encoding(raw_content)
            
            # 2. Extract main content
            main_content = self.extract_main_content(content)
            
            # 3. Clean markdown
            cleaned_markdown = self.clean_markdown(main_content)
            
            # 4. Final quality check
            return cleaned_markdown if self.is_quality_content(cleaned_markdown) else None
        
        except Exception as e:
            logging.error(f"Content processing error for {url}: {e}")
            return None

    def _handle_encoding(self, content: str) -> str:
        """
        Robust encoding management for Malayalam content
        """
        if isinstance(content, bytes):
            try:
                content = content.decode('utf-8')
            except UnicodeDecodeError:
                # Fallback encoding strategies
                encodings = ['utf-8', 'iso-8859-1', 'latin1']
                for encoding in encodings:
                    try:
                        content = content.decode(encoding)
                        break
                    except:
                        continue
        
        return unicodedata.normalize('NFC', content)