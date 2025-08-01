#!/usr/bin/env python3
"""Monitor Reddit for automation showcases and builds"""

import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime, timedelta

class RedditShowcaseMonitor:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # Subreddits focused on showcasing automation
        self.subreddits = [
            'automation',
            'n8n', 
            'nocode',
            'selfhosted',
            'homeautomation',
            'sideproject',
            'somethingimade',
            'webdev'
        ]
        
    def get_showcase_posts(self, subreddit, limit=10):
        """Get showcase posts from a subreddit"""
        posts = []
        
        try:
            # Try RSS feed first (more reliable)
            rss_url = f"https://www.reddit.com/r/{subreddit}/.rss"
            response = requests.get(rss_url, headers=self.headers)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'xml')
                entries = soup.find_all('entry')
                
                for entry in entries[:limit]:
                    title = entry.find('title').text if entry.find('title') else ""
                    link = entry.find('link')['href'] if entry.find('link') else ""
                    content = entry.find('content').text if entry.find('content') else ""
                    
                    # Check if it's a showcase post
                    if self.is_showcase_post(title, content):
                        post = {
                            'title': title,
                            'url': link,
                            'content': content[:500],  # First 500 chars
                            'subreddit': subreddit,
                            'showcase_score': self.calculate_showcase_score(title, content),
                            'apps': self.extract_apps(title + " " + content)
                        }
                        posts.append(post)
                        
        except Exception as e:
            print(f"Error fetching r/{subreddit}: {e}")
            
        return posts
    
    def is_showcase_post(self, title, content):
        """Determine if post is showcasing something built"""
        showcase_indicators = [
            # Direct showcase language
            'i built', 'i made', 'i created', 'built a', 'made a', 'created a',
            'my automation', 'my workflow', 'my project', 'my bot',
            'show off', 'sharing my', 'check out my',
            
            # Success stories
            'automated my', 'saves me', 'saved me', 'hours saved',
            'finally automated', 'workflow that',
            
            # Tutorial/guide language  
            'how i automated', 'tutorial:', 'guide:', 'walkthrough',
            'step by step', 'here\'s how',
            
            # Questions about specific implementations
            'anyone else automate', 'what do you use to automate',
            'best way to automate'
        ]
        
        text = (title + " " + content).lower()
        
        for indicator in showcase_indicators:
            if indicator in text:
                return True
                
        return False
    
    def calculate_showcase_score(self, title, content):
        """Calculate how likely this is a good showcase (0-10)"""
        score = 0
        text = (title + " " + content).lower()
        
        # High value indicators
        high_value = [
            'saved hours', 'saved time', 'automated away', 
            'no longer need to', 'eliminates the need',
            'tutorial', 'guide', 'walkthrough', 'how i',
            'github', 'code', 'screenshot', 'demo'
        ]
        
        # Medium value indicators  
        medium_value = [
            'workflow', 'automation', 'n8n', 'zapier', 'make.com',
            'slack', 'gmail', 'sheets', 'airtable', 'notion'
        ]
        
        # Metrics mentioned
        if re.search(r'\d+\s*(?:hours?|minutes?|days?)', text):
            score += 3
        if re.search(r'\d+%', text):
            score += 2
            
        # Keywords
        for keyword in high_value:
            if keyword in text:
                score += 2
                
        for keyword in medium_value:
            if keyword in text:
                score += 1
                
        return min(score, 10)  # Cap at 10
    
    def extract_apps(self, text):
        """Extract mentioned apps/tools"""
        apps = []
        text_lower = text.lower()
        
        app_patterns = {
            'n8n': 'n8n',
            'zapier': 'Zapier', 
            'make.com': 'Make.com',
            'ifttt': 'IFTTT',
            'slack': 'Slack',
            'discord': 'Discord',
            'gmail': 'Gmail',
            'google sheets': 'Google Sheets',
            'airtable': 'Airtable',
            'notion': 'Notion',
            'trello': 'Trello',
            'asana': 'Asana',
            'stripe': 'Stripe',
            'shopify': 'Shopify',
            'webhook': 'Webhooks',
            'api': 'API',
            'python': 'Python',
            'node.js': 'Node.js',
            'docker': 'Docker',
            'raspberry pi': 'Raspberry Pi',
            'home assistant': 'Home Assistant'
        }
        
        for pattern, app_name in app_patterns.items():
            if pattern in text_lower:
                apps.append(app_name)
                
        return apps[:5]  # Limit to 5 apps
    
    def get_all_showcases(self, posts_per_subreddit=5):
        """Get showcase posts from all monitored subreddits"""
        all_posts = []
        
        print("🔍 Scanning Reddit for automation showcases...")
        
        for subreddit in self.subreddits:
            print(f"  Checking r/{subreddit}...")
            posts = self.get_showcase_posts(subreddit, posts_per_subreddit)
            all_posts.extend(posts)
            
        # Sort by showcase score
        all_posts.sort(key=lambda x: x['showcase_score'], reverse=True)
        
        return all_posts
    
    def get_curated_showcases(self):
        """Get manually curated showcase examples"""
        showcases = [
            {
                'title': 'Automated my entire client onboarding process',
                'description': 'Built a system that takes new clients from contract to first meeting automatically',
                'apps': ['Gmail', 'Calendly', 'Airtable', 'Slack', 'DocuSign'],
                'workflow': 'Contract signed → Create Airtable record → Send welcome email → Schedule onboarding call → Set up Slack channel → Generate project folder',
                'impact': 'Reduced onboarding time from 3 days to 30 minutes',
                'complexity': 'Intermediate',
                'reddit_style': 'r/entrepreneur style post'
            },
            {
                'title': 'My apartment hunting bot that found me the perfect place',
                'description': 'Scrapes rental listings, filters by criteria, and sends me the good ones instantly',
                'apps': ['Python', 'BeautifulSoup', 'Telegram', 'Google Sheets'],
                'workflow': 'Scrape listings every 15 min → Filter by price/location/size → Check against blacklist → Send to Telegram → Log to sheet',
                'impact': 'Found apartment 2 weeks faster than manual searching',
                'complexity': 'Advanced',
                'reddit_style': 'r/python style post'
            },
            {
                'title': 'How I automated my side hustle to run itself',
                'description': 'Print-on-demand business that processes orders, manages inventory, and handles customer service',
                'apps': ['Shopify', 'Printful', 'Gmail', 'Slack', 'Google Sheets'],
                'workflow': 'Order placed → Auto-fulfill via Printful → Update inventory → Send tracking email → Handle refunds → Weekly reports',
                'impact': '$2K/month passive income, 95% automated',
                'complexity': 'Intermediate',
                'reddit_style': 'r/sidehustle style post'
            },
            {
                'title': 'Turned my morning routine into a smart home symphony',
                'description': 'Alarm triggers a chain of smart devices to ease me into the day',
                'apps': ['Home Assistant', 'Philips Hue', 'Spotify', 'Weather API', 'Coffee Maker'],
                'workflow': 'Alarm → Lights gradually brighten → Start coffee → Play music → Show weather → Warm bathroom → Open blinds',
                'impact': 'Actually enjoy waking up now, consistent routine',
                'complexity': 'Beginner',
                'reddit_style': 'r/homeautomation style post'
            }
        ]
        
        return showcases

def main():
    monitor = RedditShowcaseMonitor()
    
    print("🔥 Reddit Automation Showcases")
    print("=" * 50)
    
    # Try to get real Reddit posts
    live_posts = monitor.get_all_showcases(posts_per_subreddit=3)
    
    if live_posts:
        print(f"\n📋 Found {len(live_posts)} showcase posts:")
        for i, post in enumerate(live_posts[:5], 1):
            print(f"\n{i}. {post['title']}")
            print(f"   📍 r/{post['subreddit']}")
            print(f"   🎯 Score: {post['showcase_score']}/10")
            if post['apps']:
                print(f"   🛠️  {' + '.join(post['apps'])}")
            print(f"   🔗 {post['url']}")
    
    # Always show curated examples
    curated = monitor.get_curated_showcases()
    
    print(f"\n🌟 Curated Reddit-Style Showcases:")
    for i, showcase in enumerate(curated, 1):
        print(f"\n{i}. {showcase['title']}")
        print(f"   📝 {showcase['description']}")
        print(f"   🛠️  {' + '.join(showcase['apps'])}")
        print(f"   ⚡ Flow: {showcase['workflow']}")
        print(f"   📊 Impact: {showcase['impact']}")
        print(f"   🎯 Complexity: {showcase['complexity']}")
        print(f"   📱 Style: {showcase['reddit_style']}")

if __name__ == "__main__":
    main()