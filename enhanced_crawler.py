import os
import json
import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Optional
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
import chardet
import unicodedata
import re

from config import CrawlerConfig, CacheMode
from content_processor import ContentProcessor

class MalayalamCrawler:
    def __init__(self, config: CrawlerConfig):
        self.config = config
        self.content_processor = ContentProcessor(
            similarity_threshold=config.similarity_threshold
        )
        self.malayalam_headers = {
            "Accept-Language": "ml-IN,ml;q=0.9,en-US;q=0.8,en;q=0.7",
            "Content-Language": "ml",
            "User-Agent": "MalayalamCrawler/1.0"
        }
        self._setup_directories()
        
    def _setup_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        os.makedirs(self.config.output_dir, exist_ok=True)
        os.makedirs(self.config.markdown_dir, exist_ok=True)
        if self.config.pdf_output:
            os.makedirs(os.path.join(self.config.output_dir, 'pdfs'), exist_ok=True)
        if self.config.screenshot_output:
            os.makedirs(os.path.join(self.config.output_dir, 'screenshots'), exist_ok=True)

    async def run(self, start_index: Optional[int] = None, end_index: Optional[int] = None):
        """
        Run crawler with optional URL range selection
        
        Args:
            start_index (Optional[int]): Starting index of URLs to crawl
            end_index (Optional[int]): Ending index of URLs to crawl
        """
        # Load URLs from JSON
        with open(self.config.input_json_path, 'r') as f:
            urls = json.load(f)
        
        # Use config values if not provided
        start_index = start_index if start_index is not None else self.config.start_index
        end_index = end_index if end_index is not None else self.config.end_index or len(urls)
        
        # Apply range selection
        selected_urls = urls[start_index:end_index]
        
        # Create crawler instance
        async with AsyncWebCrawler() as crawler:
            # Batch processing
            for i in range(0, len(selected_urls), self.config.batch_size):
                batch = selected_urls[i:i+self.config.batch_size]
                await self._process_batch(batch, crawler)
        
        logging.info(f"Crawling completed. Processed {len(selected_urls)} URLs.")

    async def _process_batch(self, urls: List[str], crawler: AsyncWebCrawler) -> None:
        """Process a batch of URLs concurrently with Malayalam language support."""
        browser_config = BrowserConfig(
            proxy_config=self.config.proxy_config.__dict__ if self.config.proxy_config else None,
            headless=self.config.headless
        )

        # Updated CrawlerRunConfig without 'storage_state'
        crawler_config = CrawlerRunConfig(
            pdf=self.config.pdf_output,
            screenshot=self.config.screenshot_output,
            fetch_ssl_certificate=self.config.fetch_ssl,
            cache_mode=self.config.cache_mode.value,
            verbose=True
        )

        # Pass headers directly during URL crawling
        tasks = [self._crawl_url(crawler, url, crawler_config) for url in urls]
        await asyncio.gather(*tasks)



    async def _crawl_url(self, crawler: AsyncWebCrawler, url: str, crawler_config: CrawlerRunConfig) -> None:
        """Crawl a single URL with Malayalam content handling."""
        for attempt in range(self.config.max_retries):
            try:
                result = await crawler.arun(url=url, config=crawler_config)
                
                if result.success and result.markdown:
                    # Handle Malayalam text encoding
                    content = self._handle_malayalam_encoding(result.markdown)
                    cleaned_content = self.content_processor.clean_markdown(content)
                    
                    if not self.content_processor.is_duplicate_content(cleaned_content):
                        filename = f"{self._url_to_filename(url)}.md"
                        filepath = os.path.join(self.config.markdown_dir, filename)
                        
                        # Save with proper encoding for Malayalam
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(cleaned_content)
                        
                        self.content_processor.add_content(cleaned_content)
                        logging.info(f"Successfully saved Malayalam content from {url}")
                    else:
                        logging.info(f"Skipped duplicate Malayalam content from {url}")
                    break
                    
            except Exception as e:
                logging.error(f"Error processing {url} (attempt {attempt + 1}/{self.config.max_retries}): {str(e)}")
                if attempt == self.config.max_retries - 1:
                    logging.error(f"Max retries reached for {url}")
                await asyncio.sleep(2 ** attempt)  # Exponential backoff

    def _handle_malayalam_encoding(self, content: str) -> str:
        """Handle Malayalam text encoding issues."""
        try:
            # Detect the encoding if it's bytes
            if isinstance(content, bytes):
                detected = chardet.detect(content)
                content = content.decode(detected['encoding'] or 'utf-8')
            
            # Normalize Malayalam text
            return unicodedata.normalize('NFC', content)
            
        except Exception as e:
            logging.error(f"Error handling Malayalam encoding: {str(e)}")
            return content

    @staticmethod
    def _url_to_filename(url: str) -> str:
        """Convert URL to a safe filename, preserving Malayalam characters."""
        # Keep Malayalam characters while replacing unsafe characters
        safe_name = re.sub(r'[^\w\u0D00-\u0D7F\-_]', '_', url)
        return safe_name[:200]