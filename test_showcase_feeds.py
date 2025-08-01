#!/usr/bin/env python3
"""Test workflow showcase RSS feeds"""

import feedparser
import time

showcase_feeds = [
    ("n8n Workflows", "https://n8n.io/workflows/rss"),
    ("n8n Workflows Feed", "https://n8n.io/workflows.rss"),
    ("GitHub n8n Workflows", "https://github.com/n8n-io/n8n-workflows-collection/commits/main.atom"),
    ("Dev.to ShowDev", "https://dev.to/feed/tag/showdev"),
    ("Product Hunt AI", "https://www.producthunt.com/feed"),
    ("IndieHackers", "https://www.indiehackers.com/feed.rss"),
    ("Awesome Automation", "https://github.com/dariubs/awesome-workflow-automation/commits/main.atom"),
]

print("Testing Workflow Showcase Feeds...")
print("=" * 60)

for name, url in showcase_feeds:
    try:
        print(f"\n🔍 {name}")
        print(f"   URL: {url}")
        
        feed = feedparser.parse(url)
        
        if hasattr(feed, 'bozo') and feed.bozo:
            print(f"   ❌ Parse error")
            continue
            
        if not feed.entries:
            print(f"   ❌ No entries")
            continue
            
        print(f"   ✅ Working! {len(feed.entries)} entries")
        
        # Show sample entry
        if feed.entries:
            entry = feed.entries[0]
            print(f"   📝 Latest: {entry.get('title', 'No title')[:60]}...")
            
        time.sleep(0.5)
        
    except Exception as e:
        print(f"   ❌ Error: {str(e)[:50]}")