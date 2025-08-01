#!/usr/bin/env python3
"""Scrape Make.com templates for real automation workflows"""

import requests
from bs4 import BeautifulSoup
import json
import time

class MakeTemplateScraper:
    def __init__(self):
        self.base_url = "https://www.make.com/en/templates"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
    def get_templates(self, category=None, limit=20):
        """Fetch Make.com templates"""
        templates = []
        
        try:
            # Try different URLs for templates
            urls_to_try = [
                "https://www.make.com/en/templates",
                "https://www.make.com/en/integrations",
                "https://www.make.com/en/scenarios"
            ]
            
            for url in urls_to_try:
                print(f"Trying: {url}")
                response = requests.get(url, headers=self.headers)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Look for template cards
                    template_cards = soup.find_all(['div', 'article'], 
                                                 class_=lambda x: x and any(word in x.lower() for word in 
                                                                          ['template', 'scenario', 'workflow', 'card']))
                    
                    # Also look for links to specific templates
                    template_links = soup.find_all('a', href=lambda x: x and '/templates/' in x)
                    
                    print(f"Found {len(template_cards)} template cards and {len(template_links)} template links")
                    
                    # Process template links
                    for link in template_links[:limit]:
                        template_url = link['href']
                        if not template_url.startswith('http'):
                            template_url = f"https://www.make.com{template_url}"
                            
                        title = link.get_text(strip=True) or "Unnamed Template"
                        
                        template = {
                            'title': title,
                            'url': template_url,
                            'description': self.extract_description(link),
                            'apps': self.extract_apps(link)
                        }
                        
                        templates.append(template)
                        
                    if templates:
                        break
                        
        except Exception as e:
            print(f"Error scraping Make.com: {e}")
            
        return templates[:limit]
    
    def extract_description(self, element):
        """Extract description from template element"""
        # Look for description in various places
        parent = element.parent
        if parent:
            desc_elem = parent.find(['p', 'div'], class_=lambda x: x and 'desc' in x.lower())
            if desc_elem:
                return desc_elem.get_text(strip=True)[:200]
        return ""
    
    def extract_apps(self, element):
        """Extract app names from template"""
        apps = []
        text = element.get_text().lower()
        
        # Common app names to look for
        app_names = [
            'gmail', 'slack', 'google sheets', 'airtable', 'trello', 'asana',
            'shopify', 'stripe', 'twitter', 'facebook', 'instagram', 'linkedin',
            'salesforce', 'hubspot', 'mailchimp', 'notion', 'discord', 'telegram',
            'dropbox', 'google drive', 'microsoft teams', 'zoom', 'calendar'
        ]
        
        for app in app_names:
            if app in text:
                apps.append(app.title())
                
        return apps[:5]  # Limit to 5 apps
    
    def get_template_details(self, template_url):
        """Get detailed information about a specific template"""
        try:
            response = requests.get(template_url, headers=self.headers)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extract more details
                details = {
                    'description': self.get_meta_description(soup),
                    'steps': self.extract_workflow_steps(soup),
                    'benefits': self.extract_benefits(soup)
                }
                
                return details
        except:
            pass
        return {}
    
    def get_meta_description(self, soup):
        """Get meta description"""
        meta = soup.find('meta', {'name': 'description'}) or soup.find('meta', {'property': 'og:description'})
        return meta.get('content', '') if meta else ''
    
    def extract_workflow_steps(self, soup):
        """Extract workflow steps from template page"""
        steps = []
        
        # Look for numbered lists or step indicators
        step_elements = soup.find_all(['li', 'div'], 
                                    text=lambda x: x and any(word in x.lower() for word in 
                                                           ['step', 'when', 'then', 'trigger', 'action']))
        
        for elem in step_elements[:5]:
            step_text = elem.get_text(strip=True)
            if len(step_text) < 200 and step_text:
                steps.append(step_text)
                
        return steps
    
    def extract_benefits(self, soup):
        """Extract benefits/use cases"""
        benefits = []
        
        # Look for benefit indicators
        benefit_elements = soup.find_all(['li', 'p'], 
                                       text=lambda x: x and any(word in x.lower() for word in 
                                                              ['save', 'automate', 'reduce', 'improve', 'increase']))
        
        for elem in benefit_elements[:3]:
            benefit_text = elem.get_text(strip=True)
            if len(benefit_text) < 150 and benefit_text:
                benefits.append(benefit_text)
                
        return benefits

def main():
    scraper = MakeTemplateScraper()
    
    print("🔥 Scraping Make.com Templates")
    print("=" * 50)
    
    templates = scraper.get_templates(limit=10)
    
    if not templates:
        print("No templates found. Trying alternative approach...")
        
        # Manual list of popular Make.com workflow types
        manual_workflows = [
            {
                "title": "Gmail to Google Sheets Lead Capture",
                "description": "Automatically add new email leads to a Google Sheets database",
                "apps": ["Gmail", "Google Sheets"],
                "workflow": "New Gmail → Extract contact info → Add to Google Sheets → Send notification"
            },
            {
                "title": "Slack to Trello Task Creation", 
                "description": "Create Trello cards from Slack messages with specific keywords",
                "apps": ["Slack", "Trello"],
                "workflow": "Slack message with #task → Parse content → Create Trello card → Assign to team member"
            },
            {
                "title": "Instagram to Airtable Content Tracker",
                "description": "Track Instagram posts and metrics in an Airtable database",
                "apps": ["Instagram", "Airtable"],
                "workflow": "New Instagram post → Extract hashtags/metrics → Log to Airtable → Generate weekly report"
            }
        ]
        
        print("\n📋 Popular Make.com Workflow Types:")
        for i, wf in enumerate(manual_workflows, 1):
            print(f"\n{i}. {wf['title']}")
            print(f"   📝 {wf['description']}")
            print(f"   🛠️  {' + '.join(wf['apps'])}")
            print(f"   ⚡ {wf['workflow']}")
    else:
        for i, template in enumerate(templates, 1):
            print(f"\n{i}. {template['title']}")
            if template['description']:
                print(f"   📝 {template['description']}")
            if template['apps']:
                print(f"   🛠️  {' + '.join(template['apps'])}")
            print(f"   🔗 {template['url']}")
            
            # Get more details for first few templates
            if i <= 3:
                details = scraper.get_template_details(template['url'])
                if details.get('steps'):
                    print(f"   ⚡ Steps: {'; '.join(details['steps'][:3])}")
                time.sleep(1)  # Be nice to servers

if __name__ == "__main__":
    main()