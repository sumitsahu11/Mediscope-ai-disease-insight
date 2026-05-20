import re
import urllib.parse
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.nhs.uk"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-GB,en;q=0.9",
}


def make_slug(query: str) -> str: # desease name to url using slug
    slug = query.strip().lower()
    slug = re.sub(r"[^a-z0-9\s-]", " ", slug)
    slug = re.sub(r"[\s-]+", "-", slug)
    return slug.strip("-")


def extract_article_text(html: str) -> str: # Pull readable text from an NHS condition page
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup.find_all(["nav", "header", "footer", "aside",
                               "script", "style", "noscript"]):
        tag.decompose()
    for el in soup.find_all(class_=re.compile(
            r"(breadcrumb|cookie|banner|navigation|skip|back-to-top)", re.I)):
        el.decompose()


    content = (
        soup.find("article") or
        soup.find("main") or
        soup.find(id=re.compile(r"(main|content|article)", re.I)) or
        soup.find(class_=re.compile(r"(nhsuk-main-wrapper|article-body|page-section)", re.I)) or
        soup
    )

    paragraphs = []
    for p in content.find_all("p"):
        text = p.get_text(separator=" ", strip=True)
        if text and len(text) > 30:
            paragraphs.append(text)

    return " ".join(paragraphs)


def try_direct_url(slug: str) -> tuple:
    """Try fetching https://www.nhs.uk/conditions/<slug>/"""
    url = f"{BASE_URL}/conditions/{slug}/"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=12)
        if resp.status_code == 200:
            text = extract_article_text(resp.text)
            if len(text.split()) > 30:
                return text, url
    except Exception as e:
        print(f"[fetcher] Direct URL error for '{slug}': {e}")
    return None, None


def try_search_fallback(query: str) -> tuple:
    """Use NHS search to find the best condition page."""
    search_url = f"{BASE_URL}/search/results/?q={urllib.parse.quote_plus(query)}"
    try:
        resp = requests.get(search_url, headers=HEADERS, timeout=12)
        resp.raise_for_status()
    except Exception as e:
        print(f"[fetcher] Search page error: {e}")
        return None, None

    soup = BeautifulSoup(resp.text, "html.parser")
    query_lower = query.lower()

    candidates = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "/conditions/" not in href:
            continue

        text = a.get_text(strip=True).lower()

        if any(skip in text for skip in ["nhs 111", "find a gp", "nhs services"]):
            continue

        score = 0
        if query_lower in text:
            score += 3
        if query_lower in href.lower():
            score += 2
        if href.count("/") == 3:  
            score += 1

        full_href = href if href.startswith("http") else urllib.parse.urljoin(BASE_URL, href)
        candidates.append((score, full_href))

    if not candidates:
        print("[fetcher] No condition links found in search results.")
        return None, None

    candidates.sort(reverse=True, key=lambda x: x[0])
    best_url = candidates[0][1]

    try:
        article_resp = requests.get(best_url, headers=HEADERS, timeout=12)
        article_resp.raise_for_status()
        text = extract_article_text(article_resp.text)
        if len(text.split()) > 30:
            return text, best_url
    except Exception as e:
        print(f"[fetcher] Article fetch error: {e}")

    return None, None


def fetch_nhs_disease_article(disease_name: str) -> tuple:

    slug = make_slug(disease_name)

    text, url = try_direct_url(slug)
    if text:
        return text, url

    alt_slugs = []
    words = slug.split("-")
    if len(words) >= 2:
        if words[0] in ("type", "stage", "grade"):
            alt_slugs.append("-".join(words[1:] + [words[0]]))

        alt_slugs.append("-".join(words[1:]))

    for alt in alt_slugs:
        if not alt:
            continue
        text, url = try_direct_url(alt)
        if text:
            return text, url

    print(f"[fetcher] Falling back to search for: '{disease_name}'")
    return try_search_fallback(disease_name)
