import requests
from bs4 import BeautifulSoup
from datetime import datetime
import csv
import os
import logging

os.makedirs("logs", exist_ok=True)
if os.path.exists("logs/crawler.log") and os.path.getsize("logs/crawler.log") > 5 * 1024 * 1024:
    open("logs/crawler.log", "w").close()

logging.basicConfig(
    filename="logs/crawler.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

def safe_parse_iso8601(dt_string):
    """
    Parse ISO 8601 timestamps, even with short fractional seconds (like .45 or .4)
    """
    from datetime import datetime
    import re

    if not dt_string:
        return None

    # Add padding to fractional seconds if needed
    if "." in dt_string:
        parts = dt_string.split(".")
        if len(parts) > 1:
            second_part = parts[1]
            if "+" in second_part or "Z" in second_part:
                time_and_offset = re.split(r'([+\-Z])', second_part, maxsplit=1)
                micros = time_and_offset[0].ljust(6, "0")  # pad to 6 digits
                offset = "".join(time_and_offset[1:]) if len(time_and_offset) > 1 else ""
                dt_string = parts[0] + "." + micros + offset
            else:
                dt_string = parts[0] + "." + second_part.ljust(6, "0")

    return datetime.fromisoformat(dt_string.replace("Z", "+00:00"))

def fetch_html(url):
    """
    Send a GET request to the provided URL and return the HTML content.
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/114.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Connection": "keep-alive"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.text
        else:
            print(f"Failed to fetch URL: {url} | Status code: {response.status_code}")
            return None
    except requests.exceptions.RequestException as error:
        print(f"Request error: {error}")
        return None

def parse_articles(html):
    """
    Parse the HTML and extract article title, timestamp, and link.
    """
    soup = BeautifulSoup(html, "html.parser")
    articles = []

    # Match all story-card <li> elements (regardless of additional classes)
    story_cards = soup.find_all("li", class_=lambda c: c and "story-card" in c)

    for tag in story_cards:
        title_tag = tag.find("span", attrs={"data-testid": "TitleHeading"})
        link_tag = tag.find("a", attrs={"data-testid": "TitleLink"})
        time_tag = tag.find("time")
        summary_tag = tag.find("p", attrs={"data-testid": "Description"})

        if not title_tag or not link_tag:
            continue

        title = title_tag.get_text(strip=True)
        relative_url = link_tag.get("href")
        summary = summary_tag.get_text(strip=True) if summary_tag else ""
        full_url = "https://www.reuters.com" + relative_url if relative_url.startswith("/") else relative_url

        try:
            if time_tag and time_tag.get("datetime"):
                timestamp = safe_parse_iso8601(time_tag["datetime"])
            else:
                timestamp = datetime.utcnow()
        except Exception as e:
            print(f"Could not parse timestamp: {e}")
            continue

        articles.append({
            "title": title,
            "timestamp": timestamp,
            "url": full_url,
            "summary": summary
        })

    return articles

def save_to_csv(articles, filename="reuters_articles.csv"):
    """
    Append articles to a CSV file. Writes headers if missing or if file doesn't exist.
    """
    fieldnames = ["timestamp", "formatted_time", "title", "url", "summary"]
    write_headers = True

    if os.path.exists(filename):
        with open(filename, mode="r", encoding="utf-8") as file:
            first_line = file.readline().strip().lower()
            expected = ",".join(fieldnames)
            if expected in first_line:
                write_headers = False

    try:
        with open(filename, mode="a", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)

            if write_headers:
                writer.writeheader()

            for article in articles:
                writer.writerow({
                    "timestamp": article["timestamp"].isoformat(),
                    "formatted_time": article["timestamp"].strftime("%B %d, %Y @ %I:%M %p"),
                    "title": article["title"],
                    "url": article["url"],
                    "summary": article["summary"]
                })

    except Exception as e:
        print(f"Error writing to CSV: {e}")

def main():
    """
    Main function to run the crawler.
    """
    target_url = "https://www.reuters.com"

    logging.info("Started crawler")
    print(f"Fetching articles from {target_url}...")

    html_content = fetch_html(target_url)

    if html_content is not None:
        articles = parse_articles(html_content)

        print(f"Found {len(articles)} articles.")
        for article in articles:
            print(f"{article['timestamp']} — {article['title']}")

        save_to_csv(articles)
        print("Articles saved to CSV.")
    else:
        print("Could not fetch or parse HTML.")

# Run the script
if __name__ == "__main__":
    main()
