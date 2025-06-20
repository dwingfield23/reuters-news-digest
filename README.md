# Reuters News Crawler & Daily Digest Generator

This project crawls Reuters news articles every 15 minutes, saving them to a CSV file, and generates a styled daily HTML digest once an hour. It’s designed as a demo for job recruiters and anyone interested in Python web scraping and automation.

---

## Features

- Crawls news articles from Reuters regularly  
- Filters and scores articles by keywords and recency  
- Saves data to CSV for historical tracking  
- Generates a clean, collapsible HTML daily digest  
- Logs activity for troubleshooting  
- Easy to customize keywords and schedule frequency

---

## Getting Started

### Prerequisites

- Python 3.7+  
- `requests`, `beautifulsoup4`, `pandas` (install via `pip install -r requirements.txt`)  

---

### Installation

1. Clone the repo:

   ```bash
   git clone https://github.com/yourusername/reuters-news-crawler.git
   cd reuters-news-crawler

## Windows Setup

For convenience, `.bat` files for scheduling tasks with Task Scheduler are included in `/bat`.

- `run_crawler.bat`: runs the news crawler
- `run_digest.bat`: runs the digest generator

Edit paths in these files to match your Python and project directory.
