import re
import logging
import unicodedata
from typing import List
from bs4 import BeautifulSoup
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class ContentProcessor:
    def __init__(self, similarity_threshold: float = 0.7):
        self.similarity_threshold = similarity_threshold
        self.vectorizer = TfidfVectorizer(stop_words='english')
        self.processed_contents: List[str] = []
        self.processed_vectors = None
        
    def clean_malayalam_content(self, content: str) -> str:
        """Comprehensive cleaning for Malayalam content."""
        # Remove HTML tags
        soup = BeautifulSoup(content, 'html.parser')
        text = soup.get_text(separator=' ')
        
        # Normalize Unicode for Malayalam
        text = unicodedata.normalize('NFC', text)
        
        # Remove extra whitespaces
        text = re.sub(r'\s+', ' ', text)
        
        # Optional: Remove non-Malayalam characters if needed
        text = re.sub(r'[^\u0D00-\u0D7F\s]', '', text)
        
        return text.strip()
    
    def clean_markdown(self, content: str) -> str:
        """Clean markdown content."""
        # Remove markdown-specific syntax
        content = re.sub(r'#+\s*', '', content)  # Remove headers
        content = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', content)  # Remove links
        content = re.sub(r'`{1,3}[^`\n]+`{1,3}', '', content)  # Remove inline code
        
        # Use existing Malayalam content cleaning
        cleaned_content = self.clean_malayalam_content(content)
        
        return cleaned_content
    
    def is_duplicate_content(self, content: str) -> bool:
        """Check if content is similar to previously processed content."""
        if not self.processed_contents:
            logging.info("No previous content to compare with.")
            return False

        # Fit the vectorizer if it hasn't been fitted yet
        if self.processed_vectors is None:
            logging.info("Fitting TF-IDF vectorizer on processed contents.")
            self.processed_vectors = self.vectorizer.fit_transform(self.processed_contents)

        # Vectorize new content
        new_vector = self.vectorizer.transform([content])

        # Calculate similarities
        similarities = cosine_similarity(new_vector, self.processed_vectors)
        max_similarity = np.max(similarities)

        logging.info(f"Max similarity with previous content: {max_similarity}")
        return max_similarity > self.similarity_threshold
    
    def add_content(self, content: str) -> None:
        """Add processed content to tracked contents."""
        self.processed_contents.append(content)
        self.processed_vectors = None