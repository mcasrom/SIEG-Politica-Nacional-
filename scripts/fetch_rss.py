#!/usr/bin/env python3
import json
import os
import datetime
import feedparser

BASE_DIR = os.path.expanduser("~/SIEG-Politica-Nacional")
CONFIG_PATH = os.path.join(BASE_DIR, "config", "feeds_rss.json")
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
LOG_PATH = os.path.join(BASE_DIR, "logs", "pipeline.log")

os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)

def log(msg):
    ts = datetime.datetime.now().isoformat()
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"[{ts}] [FETCH] {msg}\n")

def load_feeds():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)["feeds"]

def fetch_all():
    feeds = load_feeds()
    all_entries = []
    for feed in feeds:
        log(f"Fetching {feed['name']} - {feed['url']}")
        d = feedparser.parse(feed["url"])
        for entry in d.entries:
            all_entries.append({
                "source": feed["name"],
                "source_type": feed.get("type", "medio"),
                "title": entry.get("title", ""),
                "summary": entry.get("summary", ""),
                "link": entry.get("link", ""),
                "published": entry.get("published", "")
            })
    return all_entries

def save_raw(entries):
    date_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(RAW_DIR, f"rss_raw_{date_str}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)
    log(f"Saved {len(entries)} entries to {path}")
    return path

if __name__ == "__main__":
    try:
        entries = fetch_all()
        save_raw(entries)
    except Exception as e:
        log(f"ERROR: {e}")
