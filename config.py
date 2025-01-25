# config.py
import os
from dataclasses import dataclass, field
from typing import Optional, Dict, List
from enum import Enum

class CacheMode(Enum):
    """Defines how caching should be handled during crawling."""
    BYPASS = "bypass"        # Ignore cache completely
    USE_CACHE = "use_cache"  # Use existing cache if available
    UPDATE_CACHE = "update_cache"  # Update cache with new data

@dataclass
class ProxyConfig:
    """Configuration for proxy servers with rotation support."""
    server: str
    username: Optional[str] = None
    password: Optional[str] = None
    country: Optional[str] = None  # Additional country info
    anonymity_level: Optional[str] = None  # High, Medium, Low

@dataclass
class CrawlerConfig:
    """Comprehensive configuration for web crawler."""
    input_json_path: str = "urls.json"
    output_dir: str = "output"
    markdown_dir: str = "markdown_output"
    
    # Crawling Parameters
    batch_size: int = 5
    start_index: int = 0
    end_index: Optional[int] = None
    
    # Proxy and Network Settings
    proxy_list_path: Optional[str] = "good_proxies.txt"
    proxy_rotation_strategy: str = "round_robin"  # Other strategies: random, weighted
    
    # Browser and Crawling Configurations
    headless: bool = True
    pdf_output: bool = True
    screenshot_output: bool = True
    fetch_ssl: bool = True
    
    # Advanced Settings
    cache_mode: CacheMode = CacheMode.BYPASS
    custom_headers: Optional[Dict[str, str]] = field(default_factory=lambda: {
        "Accept-Language": "ml-IN,ml;q=0.9",
        "User-Agent": "MalayalamCrawler/1.0"
    })
    
    storage_state: Optional[str] = None
    similarity_threshold: float = 0.85
    max_retries: int = 3
    timeout: int = 30
    
    def load_proxies(self) -> List[str]:
        """Load and validate proxies from a text file."""
        if not self.proxy_list_path or not os.path.exists(self.proxy_list_path):
            return []
        
        with open(self.proxy_list_path, 'r') as f:
            proxies = [line.strip() for line in f.readlines() 
                       if line.strip() and self._validate_proxy(line.strip())]
        return proxies
    
    def _validate_proxy(self, proxy: str) -> bool:
        """Basic proxy validation."""
        try:
            # Check if proxy is in correct format (IP:PORT)
            ip, port = proxy.split(':')
            int(port)  # Ensure port is a number
            return True
        except (ValueError, TypeError):
            return False