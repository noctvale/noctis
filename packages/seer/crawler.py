import logging
import time
import random
import urllib.parse
import traceback

from fake_useragent import UserAgent

from playwright.sync_api import sync_playwright
from collections import deque
from datetime import datetime
from bs4 import BeautifulSoup


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class Crawler:
    def __init__(self, seed_urls=[], max_depth=1, max_pages=100, max_retries=3, max_scrolls=10, collector=None):
        self.urls = deque([[url, 0] for url in seed_urls])
        self.visited_urls = set()
        self.start_time = datetime.now()

        self.max_depth = max_depth
        self.max_pages = max_pages
        self.max_retries = max_retries
        self.max_scrolls = max_scrolls

        self.collector = collector

        self.browser_configuration = {
            "headless": True,
            "args": [
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-web-security",
                "--disable-features=site-per-process",
            ],
        }

    def crawl(self):
        try:
            logger.debug(f"Starting crawler {datetime.now()}")
            logger.debug(f"Total URLs : {len(self.urls)}")
            logger.debug(f"Max depth : {self.max_depth}")
            logger.debug(f"Max pages : {self.max_pages}")
            logger.debug(f"Max retries : {self.max_retries}")
            logger.debug(f"Browser configuration : {self.browser_configuration}")

            while self.urls:
                url, depth = self.urls.popleft()

                if len(self.urls) >= self.max_pages:
                    logger.debug(f"Max pages is reached")
                    break

                if url in self.visited_urls:
                    logger.debug(f"Skipping {url} because it has been visited")
                    continue

                if depth >= self.max_depth:
                    logger.debug(f"Skipping {url} because depth is greater than max depth")
                    continue

                self.visited_urls.add(url)

                with sync_playwright() as playwright:
                    browser = playwright.chromium.launch(**self.browser_configuration)
                    context = browser.new_context()
                    page = context.new_page()
                    for attempt in range(self.max_retries):
                        try:
                            page.goto(url)
                            page.wait_for_load_state("domcontentloaded")
                            page.wait_for_load_state("networkidle")


                            previous_page_height = 0
                            for _ in range(self.max_scrolls):
                                page_height = page.evaluate("document.body.scrollHeight")
                                logger.debug(f"Page height : {page_height}")
                                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")

                                if page_height == previous_page_height:
                                    break

                                previous_page_height = page_height

                                time.sleep(random.uniform(0.5, 1.5))

                                page.wait_for_load_state("domcontentloaded")
                                page.wait_for_load_state("networkidle")
                                page_height = page.evaluate("document.body.scrollHeight")

                            content = page.content()
                            soup = BeautifulSoup(content, "html.parser")

                            links = soup.find_all("a")
                            for link in links:
                                href = link.get("href")

                                if href.startswith("//"):
                                    href = "https:" + href
                                elif href.startswith("/"):
                                    href = url + href


                                if not href.startswith("http"):
                                    continue
                                self.urls.append([href, depth + 1])

                            self.collector(content)

                            logger.info(f"Crawled {url} in {datetime.now() - self.start_time}")
                            break
                        except Exception as e:
                            time.sleep(attempt ** 2)
                            logger.error(traceback.format_exc())
                            logger.error(f"Error fetching {url}: {e}")
                            continue

                    page.close()
                    browser.close() 
                logger.info(f"Crawler finished in {datetime.now() - self.start_time}")
        except Exception as e:
            logger.error(f"Error crawling: {e}")
            raise e
                        