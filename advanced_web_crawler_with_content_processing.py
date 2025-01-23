# config.py
import os
from dataclasses import dataclass
from typing import Optional, Dict, Any
from enum import Enum

class CacheMode(Enum):
    BYPASS = "bypass"
    USE_CACHE = "use_cache"
    UPDATE_CACHE = "update_cache"

@dataclass
class ProxyConfig:
    server: str
    username: Optional[str] = None
    password: Optional[str] = None
    
@dataclass
class CrawlerConfig:
    input_json_path: str
    output_dir: str
    markdown_dir: str
    batch_size: int = 10
    start_index: int = 0
    end_index: Optional[int] = None
    proxy_config: Optional[ProxyConfig] = None
    headless: bool = True
    pdf_output: bool = False
    screenshot_output: bool = False
    fetch_ssl: bool = True
    cache_mode: CacheMode = CacheMode.BYPASS
    custom_headers: Optional[Dict[str, str]] = None
    storage_state: Optional[str] = None
    similarity_threshold: float = 0.85
    max_retries: int = 3
    timeout: int = 30