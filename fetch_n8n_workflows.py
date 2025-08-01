#!/usr/bin/env python3
"""Fetch real n8n workflows from community and examples"""

import requests
from bs4 import BeautifulSoup
import json
import re

class N8nWorkflowFetcher:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
    def get_community_workflows(self, limit=10):
        """Fetch workflows from n8n community"""
        workflows = []
        
        # Community URLs to try
        community_urls = [
            "https://community.n8n.io/c/workflows/8",
            "https://community.n8n.io/c/show/12",
            "https://community.n8n.io/latest"
        ]
        
        for url in community_urls:
            try:
                print(f"Fetching from: {url}")
                response = requests.get(url, headers=self.headers)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Look for topic/post links
                    topic_links = soup.find_all('a', href=lambda x: x and ('/t/' in x or 'topic' in x))
                    
                    for link in topic_links[:limit]:
                        title = link.get_text(strip=True)
                        if title and len(title) > 10:  # Filter out short/empty titles
                            workflow_url = link['href']
                            if not workflow_url.startswith('http'):
                                workflow_url = f"https://community.n8n.io{workflow_url}"
                            
                            workflow = {
                                'title': title,
                                'url': workflow_url,
                                'source': 'n8n Community',
                                'apps': self.extract_apps_from_title(title),
                                'category': self.categorize_workflow(title)
                            }
                            
                            workflows.append(workflow)
                            
                if workflows:
                    break
                    
            except Exception as e:
                print(f"Error fetching from {url}: {e}")
                continue
                
        return workflows[:limit]
    
    def extract_apps_from_title(self, title):
        """Extract app names from workflow title"""
        apps = []
        title_lower = title.lower()
        
        # Popular n8n integrations
        app_keywords = {
            'slack': 'Slack',
            'gmail': 'Gmail',
            'google sheets': 'Google Sheets',
            'google drive': 'Google Drive',
            'airtable': 'Airtable',
            'notion': 'Notion',
            'trello': 'Trello',
            'discord': 'Discord',
            'telegram': 'Telegram',
            'stripe': 'Stripe',
            'shopify': 'Shopify',
            'hubspot': 'HubSpot',
            'salesforce': 'Salesforce',
            'mailchimp': 'Mailchimp',
            'twitter': 'Twitter',
            'linkedin': 'LinkedIn',
            'facebook': 'Facebook',
            'instagram': 'Instagram',
            'youtube': 'YouTube',
            'dropbox': 'Dropbox',
            'jira': 'Jira',
            'asana': 'Asana',
            'monday': 'Monday.com',
            'clickup': 'ClickUp',
            'webhook': 'Webhook',
            'api': 'API',
            'rss': 'RSS',
            'csv': 'CSV',
            'mysql': 'MySQL',
            'postgres': 'PostgreSQL',
            'mongodb': 'MongoDB'
        }
        
        for keyword, app_name in app_keywords.items():
            if keyword in title_lower:
                apps.append(app_name)
                
        return apps[:4]  # Limit to 4 apps
    
    def categorize_workflow(self, title):
        """Categorize workflow based on title"""
        title_lower = title.lower()
        
        categories = {
            'data sync': ['sync', 'import', 'export', 'backup'],
            'notifications': ['alert', 'notify', 'notification', 'remind'],
            'social media': ['twitter', 'facebook', 'instagram', 'linkedin', 'social'],
            'e-commerce': ['shopify', 'stripe', 'order', 'customer', 'product'],
            'project management': ['trello', 'asana', 'jira', 'task', 'project'],
            'marketing': ['mailchimp', 'campaign', 'email marketing', 'lead'],
            'content': ['rss', 'blog', 'content', 'post', 'article'],
            'integration': ['api', 'webhook', 'connect', 'integration']
        }
        
        for category, keywords in categories.items():
            if any(keyword in title_lower for keyword in keywords):
                return category
                
        return 'automation'
    
    def get_workflow_examples(self):
        """Get predefined workflow examples"""
        examples = [
            {
                'title': 'Slack Alert for Website Downtime',
                'description': 'Monitor website status and send Slack alerts when down',
                'apps': ['HTTP Request', 'Slack'],
                'workflow': 'Every 5 min → Check website status → If down → Send Slack alert → Log to Google Sheets',
                'impact': 'Reduced downtime response from 30 min to 5 min',
                'complexity': 'Beginner',
                'time_to_build': '15 minutes'
            },
            {
                'title': 'RSS to Discord News Bot',
                'description': 'Automatically post new articles from RSS feeds to Discord',
                'apps': ['RSS', 'Discord', 'Google Sheets'],
                'workflow': 'Every hour → Check RSS feeds → Filter new posts → Format message → Post to Discord → Save to sheet',
                'impact': 'Eliminated 2 hours daily of manual news sharing',
                'complexity': 'Intermediate',
                'time_to_build': '30 minutes'
            },
            {
                'title': 'Gmail Attachment Backup System',
                'description': 'Automatically save Gmail attachments to Google Drive',
                'apps': ['Gmail', 'Google Drive'],
                'workflow': 'New Gmail with attachment → Extract files → Upload to Drive folder → Send confirmation',
                'impact': 'Never lose important documents, saved 1 hour weekly',
                'complexity': 'Beginner',
                'time_to_build': '20 minutes'
            },
            {
                'title': 'Customer Feedback Analyzer',
                'description': 'Analyze customer feedback and route to appropriate teams',
                'apps': ['Gmail', 'OpenAI', 'Slack', 'Airtable'],
                'workflow': 'New feedback email → OpenAI sentiment analysis → Route to team → Log in Airtable → Slack notification',
                'impact': '90% faster feedback processing, improved customer satisfaction',
                'complexity': 'Advanced',
                'time_to_build': '45 minutes'
            },
            {
                'title': 'Social Media Cross-Poster',
                'description': 'Post content across multiple social platforms simultaneously',
                'apps': ['Twitter', 'LinkedIn', 'Facebook', 'Buffer'],
                'workflow': 'Content trigger → Customize for each platform → Schedule posts → Track engagement → Report results',
                'impact': '5x content reach, 3 hours saved weekly',
                'complexity': 'Intermediate',
                'time_to_build': '35 minutes'
            }
        ]
        
        return examples

def main():
    fetcher = N8nWorkflowFetcher()
    
    print("🔥 n8n Workflow Examples")
    print("=" * 50)
    
    # Try to get community workflows
    community_workflows = fetcher.get_community_workflows(limit=5)
    
    if community_workflows:
        print("\n📋 From n8n Community:")
        for i, wf in enumerate(community_workflows, 1):
            print(f"\n{i}. {wf['title']}")
            if wf['apps']:
                print(f"   🛠️  {' + '.join(wf['apps'])}")
            print(f"   📂 {wf['category']}")
            print(f"   🔗 {wf['url']}")
    else:
        print("\nCommunity workflows not accessible, showing examples...")
        
    # Always show curated examples
    examples = fetcher.get_workflow_examples()
    
    print("\n🌟 Proven n8n Workflow Examples:")
    for i, example in enumerate(examples, 1):
        print(f"\n{i}. {example['title']}")
        print(f"   📝 {example['description']}")
        print(f"   🛠️  {' + '.join(example['apps'])}")
        print(f"   ⚡ Flow: {example['workflow']}")
        print(f"   📊 Impact: {example['impact']}")
        print(f"   🎯 Complexity: {example['complexity']} ({example['time_to_build']})")

if __name__ == "__main__":
    main()