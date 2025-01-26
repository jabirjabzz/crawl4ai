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
from content_processor import AdvancedContentProcessor  # Updated import

class MalayalamCrawler:
    def __init__(self, config: CrawlerConfig):
        """
        Initialize the Malayalam web crawler with advanced configuration
        
        Key Components:
        - Configurable crawling parameters
        - Advanced content processing
        - Multilingual headers
        - Concurrent processing support
        """
        self.config = config
        
        # Use the Advanced Content Processor for intelligent extraction
        self.content_processor = AdvancedContentProcessor(
            similarity_threshold=config.similarity_threshold
        )
        
        # Enhanced malayalam-specific headers
        self.malayalam_headers = {
            "Accept-Language": "ml-IN,ml;q=0.9,en-US;q=0.3",
            "Content-Language": "ml",
            "User-Agent": "MalayalamContentExtractor/2.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }
        
        # Setup necessary directories
        self._setup_directories()
        
        # Concurrency control
        self.semaphore = asyncio.Semaphore(self.config.batch_size)
        
        # Logging setup
        self.logger = logging.getLogger(__name__)

    def _setup_directories(self) -> None:
        """
        Create output directories with clear, organized structure
        
        Ensures consistent directory layout for:
        - Markdown output
        - Optional PDF and screenshot storage
        """
        os.makedirs(self.config.output_dir, exist_ok=True)
        os.makedirs(self.config.markdown_dir, exist_ok=True)
        
        # Optional output directories
        if self.config.pdf_output:
            os.makedirs(os.path.join(self.config.output_dir, 'pdfs'), exist_ok=True)
        if self.config.screenshot_output:
            os.makedirs(os.path.join(self.config.output_dir, 'screenshots'), exist_ok=True)

    async def run(self, start_index: Optional[int] = None, end_index: Optional[int] = None):
        """
        Orchestrate the web crawling process
        
        Features:
        - Flexible URL range selection
        - Batch processing
        - Error resilience
        """
        # Load URLs from configuration file
        with open(self.config.input_json_path, 'r', encoding='utf-8') as f:
            urls = json.load(f)
        
        # Apply default or specified URL range
        start_index = start_index if start_index is not None else self.config.start_index
        end_index = end_index if end_index is not None else self.config.end_index or len(urls)
        
        selected_urls = urls[start_index:end_index]
        
        # Concurrent crawling using AsyncWebCrawler
        async with AsyncWebCrawler() as crawler:
            tasks = [self._process_url(crawler, url) for url in selected_urls]
            await asyncio.gather(*tasks)
        
        self.logger.info(f"Crawling completed. Processed {len(selected_urls)} URLs.")

    async def _process_url(self, crawler: AsyncWebCrawler, url: str) -> None:
        """
        Process a single URL with concurrency and error handling
        
        Ensures:
        - Controlled concurrent processing
        - Retry mechanism
        - Comprehensive error logging
        """
        async with self.semaphore:
            await self._crawl_url(crawler, url)

    async def _crawl_url(self, crawler: AsyncWebCrawler, url: str) -> None:
        """
        Advanced URL crawling with intelligent content extraction
        
        Key Features:
        - Robust error handling
        - Configurable crawling parameters
        - Intelligent content filtering
        - Optional PDF and screenshot capture
        """
        for attempt in range(self.config.max_retries):
            try:
                # Crawler configuration with fine-tuned parameters
                crawler_config = CrawlerRunConfig(
                    pdf=self.config.pdf_output,
                    screenshot=self.config.screenshot_output,
                    fetch_ssl_certificate=self.config.fetch_ssl,
                    cache_mode=self.config.cache_mode.value,
                    verbose=True
                )

                # Execute web crawling with custom headers
                result = await crawler.arun(
                    url=url, 
                    config=crawler_config, 
                    headers=self.malayalam_headers
                )
                
                # Process successful crawl
                if result.success:
                    # Process markdown content
                    if result.markdown:
                        processed_content = self.content_processor.process_webpage_content(url, result.markdown)
                        
                        # Save high-quality content
                        if processed_content:
                            markdown_filename = f"{self._url_to_filename(url)}.md"
                            markdown_path = os.path.join(self.config.markdown_dir, markdown_filename)
                            
                            with open(markdown_path, 'w', encoding='utf-8') as f:
                                f.write(processed_content)
                            
                            self.logger.info(f"High-quality markdown saved: {markdown_path}")
                        else:
                            self.logger.info(f"No high-quality content extracted from: {url}")

                    # Optional: PDF and Screenshot handling
                    if self.config.pdf_output and result.pdf:
                        pdf_filename = f"{self._url_to_filename(url)}.pdf"
                        pdf_path = os.path.join(self.config.output_dir, 'pdfs', pdf_filename)
                        
                        with open(pdf_path, 'wb') as f:
                            f.write(result.pdf if isinstance(result.pdf, bytes) else result.pdf.encode('utf-8'))
                        
                        self.logger.info(f"PDF saved: {pdf_path}")

                    if self.config.screenshot_output and result.screenshot:
                        screenshot_filename = f"{self._url_to_filename(url)}.png"
                        screenshot_path = os.path.join(self.config.output_dir, 'screenshots', screenshot_filename)
                        
                        with open(screenshot_path, 'wb') as f:
                            f.write(result.screenshot if isinstance(result.screenshot, bytes) else result.screenshot.encode('utf-8'))
                        
                        self.logger.info(f"Screenshot saved: {screenshot_path}")

                break  # Successful processing, exit retry loop
                    
            except Exception as e:
                self.logger.error(f"Error processing {url} (attempt {attempt + 1}/{self.config.max_retries}): {str(e)}")
                
                if attempt == self.config.max_retries - 1:
                    self.logger.error(f"Max retries reached for {url}")
                
                await asyncio.sleep(2 ** attempt)  # Exponential backoff

    @staticmethod
    def _url_to_filename(url: str) -> str:
        """
        Generate safe, unique filenames from URLs
        
        Ensures:
        - URL-safe characters
        - Consistent naming convention
        - Prevents filename conflicts
        """
        import hashlib
        safe_name = re.sub(r'[^\w\u0D00-\u0D7F\-_]', '_', url)
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        return f"{safe_name[:100]}_{url_hash}"