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
            "Accept-Language": "ml-IN,ml;q=0.7,en-US;q=0.7,en;q=0.7",
            "Content-Language": "ml",
            "User-Agent": "MalayalamCrawler/1.0"
        }
        self._setup_directories()
        self.semaphore = asyncio.Semaphore(self.config.batch_size)  # Limit concurrent requests
        
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
            tasks = [self._process_url(crawler, url) for url in selected_urls]
            await asyncio.gather(*tasks)
        
        logging.info(f"Crawling completed. Processed {len(selected_urls)} URLs.")

    async def _process_url(self, crawler: AsyncWebCrawler, url: str) -> None:
        """Process a single URL with concurrency control."""
        async with self.semaphore:
            await self._crawl_url(crawler, url)

    async def _crawl_url(self, crawler: AsyncWebCrawler, url: str) -> None:
        """Crawl a single URL with Malayalam content handling."""
        for attempt in range(self.config.max_retries):
            try:
                # Define crawler run configuration
                crawler_config = CrawlerRunConfig(
                    pdf=self.config.pdf_output,
                    screenshot=self.config.screenshot_output,
                    fetch_ssl_certificate=self.config.fetch_ssl,
                    cache_mode=self.config.cache_mode.value,
                    verbose=True
                )

                # Run the crawler with custom headers
                result = await crawler.arun(
                    url=url, 
                    config=crawler_config, 
                    headers=self.malayalam_headers
                )
                
                # Check if the crawl was successful
                if result.success:
                    # Save PDF if available
                    if self.config.pdf_output and result.pdf:
                        pdf_filename = f"{self._url_to_filename(url)}.pdf"
                        pdf_path = os.path.join(self.config.output_dir, 'pdfs', pdf_filename)
                        with open(pdf_path, 'wb') as f:
                            f.write(result.pdf if isinstance(result.pdf, bytes) else result.pdf.encode('utf-8'))
                        logging.info(f"PDF saved: {pdf_path}")

                    # Save screenshot if available
                    if self.config.screenshot_output and result.screenshot:
                        screenshot_filename = f"{self._url_to_filename(url)}.png"
                        screenshot_path = os.path.join(self.config.output_dir, 'screenshots', screenshot_filename)
                        with open(screenshot_path, 'wb') as f:
                            f.write(result.screenshot if isinstance(result.screenshot, bytes) else result.screenshot.encode('utf-8'))
                        logging.info(f"Screenshot saved: {screenshot_path}")

                    # Save markdown content if available
                    if result.markdown:
                        content = self._handle_malayalam_encoding(result.markdown)
                        cleaned_content = self.content_processor.clean_markdown(content)

                        # Check for duplicate content
                        if not self.content_processor.is_duplicate_content(cleaned_content):
                            markdown_filename = f"{self._url_to_filename(url)}.md"
                            markdown_path = os.path.join(self.config.markdown_dir, markdown_filename)
                            with open(markdown_path, 'w', encoding='utf-8') as f:
                                f.write(cleaned_content)
                            self.content_processor.add_content(cleaned_content)
                            logging.info(f"Markdown saved: {markdown_path}")
                        else:
                            logging.info(f"Skipped duplicate content from {url}")
                    break  # Exit retry loop if successful
                    
            except Exception as e:
                logging.error(f"Error processing {url} (attempt {attempt + 1}/{self.config.max_retries}): {str(e)}")
                if attempt == self.config.max_retries - 1:
                    logging.error(f"Max retries reached for {url}")
                await asyncio.sleep(2 ** attempt)  # Exponential backoff


    def _handle_malayalam_encoding(self, content: str) -> str:
        """Handle Malayalam text encoding issues."""
        try:
            if isinstance(content, bytes):
                detected = chardet.detect(content)
                content = content.decode(detected['encoding'] or 'utf-8')
            return unicodedata.normalize('NFC', content)
        except Exception as e:
            logging.error(f"Error handling Malayalam encoding: {str(e)}")
            return content

    @staticmethod
    def _url_to_filename(url: str) -> str:
        import hashlib
        safe_name = re.sub(r'[^\w\u0D00-\u0D7F\-_]', '_', url)
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        return f"{safe_name[:100]}_{url_hash}"