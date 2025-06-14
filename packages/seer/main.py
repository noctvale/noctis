import json
import argparse
import os
import logging
import hashlib


from crawler import *

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__) 


if __name__ == "__main__":
  args_parser = argparse.ArgumentParser()
  args_parser.add_argument("--seed_urls", help="Seed of urls splitted by ,", required=True, nargs="*")
  args_parser.add_argument("--max_depth", help="Maximum depth of the crawler", default=1, type=int)
  args_parser.add_argument("--max_pages", help="Maximum number of pages to crawl", default=100, type=int)
  args_parser.add_argument("--max_retries", help="Maximum number of retries", default=3, type=int)
  args_parser.add_argument("--max_scrolls", help="Maximum number of scrolls", default=10, type=int)
  args_parser.add_argument("--output_dir", help="Output directory", default="output")
  

  args = args_parser.parse_args() 

  os.makedirs(args.output_dir, exist_ok=True)

  def collector_callback(html):
    checksum = hashlib.sha256(html.encode("utf-8")).hexdigest()

    with open(os.path.join(args.output_dir, f"{checksum}.html"), "w", encoding="utf-8") as f:
      f.write(html)



  crawler = Crawler(seed_urls=args.seed_urls, collector=collector_callback, max_depth=args.max_depth, max_pages=args.max_pages, max_retries=args.max_retries)
  crawler.crawl()



