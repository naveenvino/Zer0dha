import requests
import os
import logging

logger = logging.getLogger(__name__)

# Placeholder for a generic news API endpoint and API key
NEWS_API_BASE_URL = os.environ.get("NEWS_API_BASE_URL", "https://newsapi.org/v2/everything")
NEWS_API_KEY = os.environ.get("NEWS_API_KEY")

def fetch_market_news(query: str = "stock market", language: str = "en", page_size: int = 10) -> list:
    """
    Fetches market news from a news API.

    :param query: The search query for news (e.g., "NIFTY", "Sensex", "Reliance").
    :param language: The language of the news articles (e.g., "en" for English).
    :param page_size: The number of articles to return.
    :return: A list of news articles.
    """
    if not NEWS_API_KEY:
        logger.error("NEWS_API_KEY environment variable not set.")
        return []

    params = {
        "q": query,
        "language": language,
        "pageSize": page_size,
        "apiKey": NEWS_API_KEY
    }

    try:
        response = requests.get(NEWS_API_BASE_URL, params=params)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
        data = response.json()
        articles = data.get("articles", [])
        
        # Basic processing: extract relevant fields
        processed_articles = []
        for article in articles:
            processed_articles.append({
                "title": article.get("title"),
                "description": article.get("description"),
                "url": article.get("url"),
                "source": article.get("source", {}).get("name"),
                "publishedAt": article.get("publishedAt")
            })
        return processed_articles

    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching news: {e}")
        return []
    except ValueError as e: # JSON decoding error
        logger.error(f"Error decoding news API response: {e}")
        return []

