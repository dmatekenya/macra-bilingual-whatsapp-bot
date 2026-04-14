import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse, urldefrag

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://macra.mw"

RAW_DIR = Path("/Users/dmatekenya/git-repos/macra-bilingual-whatsapp-bot/data/raw")
HTML_DIR = RAW_DIR / "html"
TEXT_DIR = RAW_DIR / "pages"
DOWNLOADS_DIR = RAW_DIR / "downloads"
MANIFEST_PATH = RAW_DIR / "crawl_manifest.jsonl"

DOWNLOADABLE_EXTENSIONS = {
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".ppt",
    ".pptx",
    ".zip",
    ".csv",
}


def classify_doc(url: str, title: str, text: str) -> str:
    combined = f"{url} {title} {text[:500]}".lower()

    if "act" in combined:
        return "act"
    if "project" in combined:
        return "project"
    if "faq" in combined:
        return "faq"
    if "consumer" in combined or "guidance" in combined:
        return "consumer_guidance"
    if "notice" in combined or "announcement" in combined:
        return "notice"
    if "form" in combined or "application" in combined:
        return "form"
    if "license" in combined or "licence" in combined:
        return "license"
    if "policy" in combined:
        return "policy"
    return "other"


def make_dirs() -> None:
    HTML_DIR.mkdir(parents=True, exist_ok=True)
    TEXT_DIR.mkdir(parents=True, exist_ok=True)
    DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)


def normalize_url(url: str) -> str:
    url = urldefrag(url)[0]
    return url.rstrip("/")


def slugify(value: str, max_length: int = 120) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^\w\s-]", "", value)
    value = re.sub(r"[-\s]+", "-", value).strip("-_")
    return value[:max_length] or "untitled"


def get_url_hash(url: str) -> str:
    return hashlib.md5(url.encode("utf-8")).hexdigest()[:12]


def is_internal_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.netloc == urlparse(BASE_URL).netloc or url.startswith(BASE_URL)


def is_downloadable_url(url: str) -> bool:
    suffix = Path(urlparse(url).path).suffix.lower()
    return suffix in DOWNLOADABLE_EXTENSIONS


def build_base_filename(url: str, title: str | None = None) -> str:
    parsed = urlparse(url)
    path_slug = slugify(Path(parsed.path).stem or (title or "page"))
    short_hash = get_url_hash(url)
    return f"{path_slug}_{short_hash}"


def extract_text_from_html(html: str) -> tuple[str, str]:
    soup = BeautifulSoup(html, "lxml")
    title = soup.title.text.strip() if soup.title and soup.title.text else "Untitled"

    text_blocks = [
        tag.get_text(" ", strip=True)
        for tag in soup.find_all(["h1", "h2", "h3", "p", "li"])
    ]
    text = "\n".join(block for block in text_blocks if block)

    return title, text


def save_text_file(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def save_binary_file(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def append_manifest(record: dict) -> None:
    with open(MANIFEST_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def handle_html_page(url: str, response: requests.Response) -> dict | None:
    html = response.text
    title, text = extract_text_from_html(html)

    if not text.strip():
        return None

    category = classify_doc(url=url, title=title, text=text)
    base_filename = build_base_filename(url=url, title=title)

    html_path = HTML_DIR / f"{base_filename}.html"
    text_path = TEXT_DIR / f"{base_filename}.txt"

    save_text_file(html_path, html)
    save_text_file(text_path, text)

    return {
        "doc_id": hashlib.md5(url.encode("utf-8")).hexdigest(),
        "title": title,
        "source_url": url,
        "content_type": response.headers.get("Content-Type", ""),
        "local_html_path": str(html_path),
        "local_text_path": str(text_path),
        "local_download_path": None,
        "category": category,
        "status": "success",
        "metadata": {
            "source_type": "webpage",
            "domain": urlparse(url).netloc,
        },
    }


def handle_download(url: str, response: requests.Response) -> dict:
    content_type = response.headers.get("Content-Type", "")
    suffix = Path(urlparse(url).path).suffix.lower() or ".bin"
    base_filename = build_base_filename(url=url)
    download_path = DOWNLOADS_DIR / f"{base_filename}{suffix}"

    save_binary_file(download_path, response.content)

    category = classify_doc(url=url, title=download_path.name, text="")

    return {
        "doc_id": hashlib.md5(url.encode("utf-8")).hexdigest(),
        "title": download_path.name,
        "source_url": url,
        "content_type": content_type,
        "local_html_path": None,
        "local_text_path": None,
        "local_download_path": str(download_path),
        "category": category,
        "status": "success",
        "metadata": {
            "source_type": "download",
            "domain": urlparse(url).netloc,
        },
    }


def fetch_url(url: str) -> requests.Response | None:
    try:
        response = requests.get(url, timeout=20)
        response.raise_for_status()
        return response
    except Exception as exc:
        append_manifest(
            {
                "doc_id": hashlib.md5(url.encode("utf-8")).hexdigest(),
                "title": None,
                "source_url": url,
                "content_type": None,
                "local_html_path": None,
                "local_text_path": None,
                "local_download_path": None,
                "category": "other",
                "status": "failed",
                "metadata": {
                    "error": str(exc),
                    "source_type": "unknown",
                    "domain": urlparse(url).netloc,
                },
            }
        )
        return None


def main() -> None:
    make_dirs()

    if MANIFEST_PATH.exists():
        MANIFEST_PATH.unlink()

    seed_urls = [BASE_URL]
    to_visit = list(seed_urls)
    seen = set()

    while to_visit:
        url = normalize_url(to_visit.pop(0))
        if url in seen:
            continue
        seen.add(url)

        print(f"Crawling: {url}")

        response = fetch_url(url)
        if response is None:
            continue

        content_type = response.headers.get("Content-Type", "").lower()

        if is_downloadable_url(url):
            record = handle_download(url, response)
            append_manifest(record)
            continue

        if "text/html" not in content_type:
            append_manifest(
                {
                    "doc_id": hashlib.md5(url.encode("utf-8")).hexdigest(),
                    "title": None,
                    "source_url": url,
                    "content_type": content_type,
                    "local_html_path": None,
                    "local_text_path": None,
                    "local_download_path": None,
                    "category": "other",
                    "status": "skipped",
                    "metadata": {
                        "reason": "unsupported_content_type",
                        "source_type": "unknown",
                        "domain": urlparse(url).netloc,
                    },
                }
            )
            continue

        page_record = handle_html_page(url, response)
        if page_record:
            append_manifest(page_record)

        soup = BeautifulSoup(response.text, "lxml")
        for a_tag in soup.find_all("a", href=True):
            next_url = normalize_url(urljoin(url, a_tag["href"]))

            if not next_url.startswith("http"):
                continue
            if not is_internal_url(next_url):
                continue
            if next_url in seen:
                continue

            to_visit.append(next_url)

    print(f"Done. Manifest saved to {MANIFEST_PATH}")
    print(f"HTML files: {HTML_DIR}")
    print(f"Text files: {TEXT_DIR}")
    print(f"Downloads: {DOWNLOADS_DIR}")


if __name__ == "__main__":
    main()