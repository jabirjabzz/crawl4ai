import asyncio
import logging
import os
from datetime import datetime

from config import CrawlerConfig, CacheMode
from enhanced_crawler import MalayalamCrawler

def setup_logging():
    """Configure comprehensive logging."""
    log_dir = 'logs'
    os.makedirs(log_dir, exist_ok=True)
    
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f'crawler_{current_time}.log')
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

async def main():
    setup_logging()
    
    try:
        config = CrawlerConfig(
            input_json_path=r"C:\Users\Administrator\Documents\GitHub\Malayalam-Language-Scraping\output_URLs\processed_urls.json",
            output_dir="output",
            markdown_dir="malayalam_output",
            pdf_output=False,  # Disable PDF if not needed
            screenshot_output=False,  # Disable screenshots if not needed
            batch_size=10,
            max_retries=3,
            cache_mode=CacheMode.BYPASS,
            similarity_threshold=0.9,
            start_index=0,
            end_index=50
        )
        # Ensure output directories exist
        os.makedirs(config.output_dir, exist_ok=True)
        os.makedirs(config.markdown_dir, exist_ok=True)
        os.makedirs(os.path.join(config.output_dir, 'pdfs'), exist_ok=True)
        os.makedirs(os.path.join(config.output_dir, 'screenshots'), exist_ok=True)
        
        crawler = MalayalamCrawler(config)
        await crawler.run(start_index=config.start_index, 
                          end_index=config.end_index)
        
        logging.info("Crawling completed successfully!")
    
    except Exception as e:
        logging.error(f"Crawler execution failed: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main())