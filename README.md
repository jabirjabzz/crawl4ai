# 🕸️ Malayalam Web Crawler: Advanced Content Harvesting Tool

## 🌟 Project Overview

This advanced web crawler is a sophisticated Python-based tool designed specifically for crawling and processing Malayalam language websites. It offers robust features for concurrent web scraping, content processing, and multilingual support.

### 🎯 Key Features

- **Concurrent Web Crawling**: Efficiently process multiple URLs simultaneously
- **Malayalam Language Support**: Specialized processing for Malayalam content
- **Proxy Rotation**: Automatic IP rotation to prevent blocking
- **Advanced Content Processing**: 
  - Duplicate content detection
  - Unicode normalization
  - Clean markdown extraction
- **Flexible Configuration**: Highly customizable crawling parameters
- **Error Handling**: Comprehensive retry and logging mechanisms

## 🛠 Technology Stack

- **Language**: Python 3.8+
- **Key Libraries**: 
  - `asyncio` for asynchronous operations
  - `crawl4ai` for web crawling
  - `scikit-learn` for content analysis
  - `beautifulsoup4` for HTML parsing

## 📋 Prerequisites

- Python 3.8 or higher
- pip package manager
- Virtual environment recommended

## 🚀 Installation

1. Clone the repository:
```bash
git clone https://github.com/jabirjabzz/malayalam-web-crawler.git
cd malayalam-web-crawler
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Unix/macOS
# Or: venv\Scripts\activate  # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## 🔧 Configuration

### URLs Configuration (`malayalam_urls.json`)
```json
[
    "https://malayalam-news-site1.com",
    "https://malayalam-blog-site2.com",
    "https://malayalam-magazine3.com"
]
```

### Proxy Configuration (`good_proxies.txt`)
```
123.45.67.89:8080
98.76.54.32:3128
12.34.56.78:80
```

## ⚙️ Customization Options

The `config.py` allows extensive customization:
- Batch size
- Proxy rotation strategy
- Content similarity threshold
- Retry attempts
- Timeout settings

## 🏃 Running the Crawler

```bash
python run_crawler.py
```

## 📂 Output Structure

- `output/`: General crawling outputs
  - `pdfs/`: PDF versions of webpages
  - `screenshots/`: Webpage screenshots
- `malayalam_output/`: Processed markdown content
- `logs/`: Detailed crawling logs

## 🔍 Advanced Features

### Content Processing
- Unicode normalization
- HTML tag removal
- Duplicate content detection using TF-IDF vectorization

### Proxy Handling
- Round-robin proxy rotation
- Random proxy selection
- Proxy validation

## 🛡️ Error Handling

- Exponential backoff for failed requests
- Comprehensive logging
- Configurable retry mechanisms

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📜 License

Distributed under the MIT License. See `LICENSE` for more information.

## 📞 Contact

Your Name - your.email@example.com

Project Link: [https://github.com/yourusername/malayalam-web-crawler](https://github.com/yourusername/malayalam-web-crawler)

## 🙏 Acknowledgments

- [Crawl4AI](https://github.com/crawl4ai/crawl4ai)
- [scikit-learn](https://scikit-learn.org/)
- Malayalam language community

---

**Disclaimer**: Ensure you have proper permissions and respect website terms of service when crawling.
