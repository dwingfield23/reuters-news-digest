import pandas as pd
import json
from datetime import datetime
from pathlib import Path
import os
import logging

# Ensure logs directory exists
os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    filename="logs/digest.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

def load_articles(filename="reuters_articles.csv"):
    columns = ["timestamp", "formatted_time", "title", "url", "summary"]
    df = pd.read_csv(filename, names=columns, header=0)
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df.dropna(subset=["timestamp"])
    return df

def load_topics(filepath="topics.json"):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Topic file '{filepath}' not found.")
        return {}

def filter_by_keywords(df, keywords):
    pattern = "|".join(keywords)
    return df[
        df["title"].str.contains(pattern, case=False, na=False) |
        df["summary"].str.contains(pattern, case=False, na=False)
    ]

def keyword_match_score(text, keywords):
    """
    Generate a 'hotness score' for.
    """
    text_lower = text.lower()
    return sum(text_lower.count(k.lower()) for k in keywords)

def get_top_trending_by_hotness(df, keywords, top_n=3):
    """
    Gets our top 3 trending articles by 'hotness'.
    """
    df = df.copy()

    # Normalize recency: newest = 1.0, oldest = 0.0
    latest = df["timestamp"].max()
    earliest = df["timestamp"].min()
    total_seconds = (latest - earliest).total_seconds()

    def recency_score(ts):
        delta = (ts - earliest).total_seconds()
        return delta / total_seconds if total_seconds else 1.0

    df["recency_score"] = df["timestamp"].apply(recency_score)

    # Count keyword matches in title and summary
    df["keyword_score"] = df.apply(
        lambda row: keyword_match_score(str(row["title"]), keywords) +
                    keyword_match_score(str(row["summary"]) if pd.notna(row["summary"]) else "", keywords),
        axis=1
    )

    # Multiply for hotness
    df["hotness"] = df["recency_score"] * df["keyword_score"]

    # Sort by hotness
    return df[df["hotness"] > 0].sort_values(by="hotness", ascending=False).head(top_n)

def get_top_trending(df, top_n=3):
    """
    Gets our top 3 trending articles from Reuters.
    """
    return df.sort_values(by="timestamp", ascending=False).head(top_n)

def save_digest(text, out_path="daily_digest.txt"):
    """
    Writes our digest.
    """
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(text)
    logging.info(f"\n Digest saved to {Path(out_path).resolve()}")
    print(f"Digest saved to {Path(out_path).resolve()}")

def generate_digest_html(df, topics):
    """
    Generates HTML digest of each topic.
    """
    from html import escape
    today = datetime.now().strftime("%B %d, %Y")

    # Combine all keywords for scoring
    all_keywords = [kw for topic_kw in topics.values() for kw in topic_kw]

    with open("digest.css", "r", encoding="utf-8") as css_file:
        css_styles = css_file.read()

    html_lines = [
        "<html>",
        "<head>",
        "<meta charset='UTF-8'>",
        f"<title>Daily News Digest — {today}</title>",
        "<style>",
        css_styles,
        "</style>",
        "</head>",
        "<body>",
        f"<h1>📊 Daily News Digest — {today}</h1>"
    ]

    # Top 3 trending articles
    top_trending = get_top_trending(df, 3)
    if not top_trending.empty:
        html_lines.append("<h2>🔥 Top 3 Trending Articles</h2>")
        html_lines.append("<ul>")
        for _, row in top_trending.iterrows():
            time_str = row["timestamp"].strftime("%I:%M %p").lstrip("0")
            title = escape(row["title"].strip())
            summary = escape(str(row["summary"]).strip()) if pd.notna(row["summary"]) else ""
            url = row["url"].strip()
            full_url = f"https://www.reuters.com{url}" if url.startswith("/") else url
            full_url = escape(full_url)

            html_lines.append(
                f"<li>"
                f"<p class='time'>[{time_str}]</p> "
                f"<a href='{full_url}' target='_blank' rel='noopener noreferrer'>{title}</a>"
            )
            if summary:
                html_lines.append(f"<p class='summary'>{summary}</p>")
            html_lines.append("</li>")
        html_lines.append("</ul>")



    # Top 3 Trending Articles by hotness
    top_trending = get_top_trending_by_hotness(df, all_keywords, top_n=3)
    if not top_trending.empty:
        html_lines.append("<h2>🔥 Top 3 Trending Articles (By Hotness Score)</h2>")
        html_lines.append("<ul>")

        for _, row in top_trending.iterrows():
            time_str = row["timestamp"].strftime("%I:%M %p").lstrip("0")
            title = escape(row["title"].strip())
            summary = escape(str(row["summary"]).strip()) if pd.notna(row["summary"]) else ""
            url = row["url"].strip()
            full_url = f"https://www.reuters.com{url}" if url.startswith("/") else url
            full_url = escape(full_url)

            html_lines.append(
                f"<li>"
                f"<p class='time'>[{time_str}]</p> "
                f"<a href='{full_url}' target='_blank' rel='noopener noreferrer'>{title}</a>"
            )
            if summary:
                html_lines.append(f"<p class='summary'>{summary}</p>")
            html_lines.append("</li>")
        html_lines.append("</ul>")

    # Topic-wise articles
    for topic, keywords in topics.items():
        matches = filter_by_keywords(df, keywords)
        if matches.empty:
            continue

        article_count = len(matches)
        topic_title = f"{escape(topic.title())} ({article_count} article{'s' if article_count != 1 else ''})"

        html_lines.append("<details>")
        html_lines.append(f"<summary>{topic_title}</summary>")
        html_lines.append("<ul style='margin-top: 10px;'>")

        for _, row in matches.iterrows():
            time_str = row["timestamp"].strftime("%I:%M %p").lstrip("0")
            title = escape(row["title"].strip())
            summary = escape(str(row["summary"]).strip()) if pd.notna(row["summary"]) else ""
            url = row["url"].strip()
            full_url = f"https://www.reuters.com{url}" if url.startswith("/") else url
            full_url = escape(full_url)

            html_lines.append(
                f"<li>"
                f"<p class='time'>[{time_str}]</p> "
                f"<a href='{full_url}' target='_blank' rel='noopener noreferrer'>{title}</a>"
            )
            if summary:
                html_lines.append(f"<p class='summary'>{summary}</p>")
            html_lines.append("</li>")

        html_lines.append("</ul>")
        html_lines.append("</details>")

    html_lines.append("</body></html>")

    return "\n".join(html_lines)

def main():
    """
    Main function to run the analyzer.
    """
    logging.info("Started digest")

    df = load_articles()
    topics = load_topics()

    if df.empty or not topics:
        logging.warning("No articles or topics to process.")
        print("No articles or topics to process.")
        exit()

    digest_html = generate_digest_html(df, topics)
    save_digest(digest_html, out_path="daily_digest.html")

if __name__ == "__main__":
    main()