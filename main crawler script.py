# main.py
import os
import json
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from base64 import b64decode
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

from config import CrawlerConfig, CacheMode
from content_processor import ContentProcessor

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('crawler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AdvancedCrawler:
    def __init__(self, config: CrawlerConfig):
        self.config = config
        self.content_processor = ContentProcessor(
            similarity_threshold=config.similarity_threshold
        )
        self._setup_directories()
        
    def _setup_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        os.makedirs(self.config.output_dir, exist_ok=True)
        os.makedirs(self.config.markdown_dir, exist_ok=True)
        if self.config.pdf_output:
            os.makedirs(os.path.join(self.config.output_dir, 'pdfs'), exist_ok=True)
        if self.config.screenshot_output:
            os.makedirs(os.path.join(self.config.output_dir, 'screenshots'), exist_ok=True)

    def _load_urls(self) -> List[str]:
        """Load URLs from JSON file."""
        try:
            with open(self.config.input_json_path, 'r') as f:
                data = json.load(f)
            
            # Handle different JSON structures
            if isinstance(data, list):
                urls = data
            elif isinstance(data, dict):
                urls = list(data.values()) if any(isinstance(v, str) for v in data.values()) else list(data.keys())
            else:
                raise ValueError("Unsupported JSON structure")
            
            # Apply range if specified
            start = self.config.start_index
            end = self.config.end_index or len(urls)
            return urls[start:end]
            
        except Exception as e:
            logger.error(f"Error loading URLs: {str(e)}")
            raise

    async def _process_batch(self, urls: List[str], crawler: AsyncWebCrawler) -> None:
        """Process a batch of URLs."""
        browser_config = BrowserConfig(
            proxy_config=self.config.proxy_config.__dict__ if self.config.proxy_config else None,
            headless=self.config.headless
        )

        crawler_config = CrawlerRunConfig(
            pdf=self.config.pdf_output,
            screenshot=self.config.screenshot_output,
            fetch_ssl_certificate=self.config.fetch_ssl,
            cache_mode=self.config.cache_mode.value,
            headers=self.config.custom_headers,
            storage_state=self.config.storage_state,
            verbose=True
        )

        tasks = []
        for url in urls:
            task = self._crawl_url(crawler, url, crawler_config)
            tasks.append(task)
        
        await asyncio.gather(*tasks)

    async def _crawl_url(self, crawler: AsyncWebCrawler, url: str, crawler_config: CrawlerRunConfig) -> None:
        """Crawl a single URL with retries."""
        for attempt in range(self.config.max_retries):
            try:
                result = await crawler.arun(url=url, config=crawler_config)
                
                if result.success:
                    # Process and save content
                    if result.markdown:
                        cleaned_content = self.content_processor.clean_markdown(result.markdown)
                        
                        if not self.content_processor.is_duplicate_content(cleaned_content):
                            # Save markdown
                            filename = f"{url_to_filename(url)}.md"
                            filepath = os.path.join(self.config.markdown_dir, filename)
                            with open(filepath, 'w', encoding='utf-8') as f:
                                f.write(cleaned_content)
                            
                            self.content_processor.add_content(cleaned_content)
                            logger.info(f"Successfully saved markdown for {url}")
                        else:
                            logger.info(f"Skipped duplicate content from {url}")
                    
                    # Save additional outputs
                    if result.pdf:
                        pdf_path = os.path.join(self.config.output_dir, 'pdfs', f"{url_to_filename(url)}.pdf")
                        with open(pdf_path, "wb") as f:
                            f.write(b64decode(result.pdf))
                    
                    if result.screenshot:
                        screenshot_path = os.path.join(self.config.output_dir, 'screenshots', f"{url_to_filename(url)}.png")
                        with open(screenshot_path, "wb") as f:
                            f.write(b64decode(result.screenshot))
                    
                    break  # Success, exit retry loop
                    
                else:
                    logger.error(f"Crawl failed for {url}: {result.error_message}")
                    
            except Exception as e:
                logger.error(f"Error processing {url} (attempt {attempt + 1}/{self.config.max_retries}): {str(e)}")
                if attempt == self.config.max_retries - 1:
                    logger.error(f"Max retries reached for {url}")
                await asyncio.sleep(2 ** attempt)  # Exponential backoff

    async def run(self) -> None:
        """Run the crawler."""
        urls = self._load_urls()
        logger.info(f"Loaded {len(urls)} URLs to process")
        
        async with AsyncWebCrawler() as crawler:
            for i in range(0, len(urls), self.config.batch_size):
                batch = urls[i:i + self.config.batch_size]
                logger.info(f"Processing batch {i//self.config.batch_size + 1}")
                await self._process_batch(batch, crawler)

def url_to_filename(url: str) -> str:
    """Convert URL to a safe filename."""
    safe_name = re.sub(r'[^\w\-_]', '_', url)
    return safe_name[:200]  # Limit filename length

async def main():
    # Load configuration
    config = CrawlerConfig(
        input_json_path="urls.json",
        output_dir="output",
        markdown_dir="markdown_output",
        batch_size=5,
        headless=True,
        pdf_output=True,
        screenshot_output=True,
        similarity_threshold=0.85
    )
    
    crawler = AdvancedCrawler(config)
    await crawler.run()

if __name__ == "__main__":
    asyncio.run(main())