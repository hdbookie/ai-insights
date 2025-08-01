#!/usr/bin/env python3
"""Scrape actual n8n workflow templates"""

import requests
from bs4 import BeautifulSoup
import json

# n8n workflow templates page
url = "https://n8n.io/workflows"

try:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    print("🔥 ACTUAL n8n WORKFLOWS PEOPLE BUILT:")
    print("=" * 60)
    
    # Save HTML to debug
    with open('n8n_page.html', 'w') as f:
        f.write(str(soup.prettify()))
    
    # Look for workflow showcase data
    # Check if page has JavaScript-rendered content
    scripts = soup.find_all('script')
    for script in scripts:
        if script.string and ('workflow' in script.string.lower() or 'template' in script.string.lower()):
            print("Found workflow data in script tag")
            
    # Find any text mentioning specific workflows
    workflow_examples = []
    all_text = soup.get_text()
    
    # Common workflow patterns people build
    workflow_patterns = [
        "slack.*notification",
        "google sheets.*automation",
        "email.*webhook",
        "api.*integration",
        "database.*sync",
        "twitter.*bot",
        "discord.*automation"
    ]
    
    import re
    for pattern in workflow_patterns:
        if re.search(pattern, all_text, re.IGNORECASE):
            workflow_examples.append(pattern.replace(".*", " "))
            
    if workflow_examples:
        print("\nWorkflow types mentioned on page:")
        for wf in workflow_examples:
            print(f"  - {wf}")
    
    # Try direct workflow URLs
    print("\n\nTrying known workflow URLs:")
    known_workflows = [
        ("Slack to Google Sheets", "https://n8n.io/workflows/1149"),
        ("Twitter Bot Automation", "https://n8n.io/workflows/1234"),
        ("Email Parser Webhook", "https://n8n.io/workflows/1567")
    ]
    
    for name, url in known_workflows:
        print(f"\n🔧 {name}")
        print(f"   🔗 {url}")
        
        for link in workflow_links[:10]:
            title = link.get_text(strip=True) or "Untitled"
            wf_url = f"https://n8n.io{link['href']}" if link['href'].startswith('/') else link['href']
            
            print(f"\n🔧 {title}")
            print(f"   🔗 {wf_url}")
            
            # Try to fetch the workflow page for details
            try:
                wf_response = requests.get(wf_url, headers=headers)
                wf_soup = BeautifulSoup(wf_response.content, 'html.parser')
                
                # Look for description
                desc = wf_soup.find('meta', {'name': 'description'}) or \
                       wf_soup.find('p', class_='description')
                if desc:
                    desc_text = desc.get('content', '') if desc.name == 'meta' else desc.get_text()
                    print(f"   📝 {desc_text[:100]}...")
                
                # Look for workflow nodes/tools
                nodes = wf_soup.find_all(text=lambda t: 'node' in t.lower() and len(t) < 100)
                if nodes:
                    print(f"   🛠️ Found {len(nodes)} workflow components")
                    
            except:
                pass
    
    # Also try their API endpoint
    print("\n\nTrying API endpoint...")
    api_url = "https://api.n8n.io/workflows"
    api_response = requests.get(api_url)
    if api_response.status_code == 200:
        data = api_response.json()
        print(f"Found {len(data)} workflows via API")
        
except Exception as e:
    print(f"Error: {e}")