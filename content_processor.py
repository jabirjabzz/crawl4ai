# content_processor.py
import re
from typing import List, Set
from bs4 import BeautifulSoup
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class ContentProcessor:
    def __init__(self, similarity_threshold: float = 0.85):
        self.similarity_threshold = similarity_threshold
        self.vectorizer = TfidfVectorizer(stop_words='english')
        self.processed_contents: List[str] = []
        self.processed_vectors = None
        
    def clean_markdown(self, content: str) -> str:
        """Clean and preprocess markdown content."""
        # Remove HTML/XML tags
        soup = BeautifulSoup(content, 'html.parser')
        text = soup.get_text()
        
        # Remove extra whitespace and normalize newlines
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        # Remove special characters but keep markdown formatting
        text = re.sub(r'[^\w\s\-_*#>\[\](){}.,;:!?]', '', text)
        
        return text.strip()
    
    def is_duplicate_content(self, content: str) -> bool:
        """Check if content is similar to previously processed content."""
        if not self.processed_contents:
            return False
            
        # Vectorize new content
        new_vector = self.vectorizer.transform([content])
        
        if self.processed_vectors is None:
            self.processed_vectors = self.vectorizer.transform(self.processed_contents)
        
        # Calculate similarities
        similarities = cosine_similarity(new_vector, self.processed_vectors)
        max_similarity = np.max(similarities)
        
        return max_similarity > self.similarity_threshold
    
    def add_content(self, content: str) -> None:
        """Add content to processed contents and update vectors."""
        self.processed_contents.append(content)
        self.processed_vectors = None  # Reset vectors to be recalculated