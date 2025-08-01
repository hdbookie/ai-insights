#!/usr/bin/env python3
"""Simple workflow database to store and organize discovered workflows"""

import json
import os
from datetime import datetime
from typing import List, Dict

class WorkflowDatabase:
    def __init__(self, db_file='workflows.json'):
        self.db_file = db_file
        self.workflows = self.load_database()
        
    def load_database(self):
        """Load workflows from JSON file"""
        if os.path.exists(self.db_file):
            try:
                with open(self.db_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return []
    
    def save_database(self):
        """Save workflows to JSON file"""
        with open(self.db_file, 'w') as f:
            json.dump(self.workflows, f, indent=2)
    
    def add_workflow(self, workflow_data):
        """Add a new workflow to database"""
        # Add metadata
        workflow_data['id'] = len(self.workflows) + 1
        workflow_data['added_date'] = datetime.now().isoformat()
        workflow_data['last_featured'] = None
        workflow_data['feature_count'] = 0
        
        self.workflows.append(workflow_data)
        self.save_database()
        
    def get_best_workflows(self, limit=10, category=None):
        """Get best workflows by score/impact"""
        filtered = self.workflows
        
        if category:
            filtered = [w for w in self.workflows if w.get('category') == category]
            
        # Sort by multiple criteria
        sorted_workflows = sorted(filtered, key=lambda x: (
            x.get('showcase_score', 0),
            len(x.get('apps', [])),
            x.get('feature_count', 0)
        ), reverse=True)
        
        return sorted_workflows[:limit]
    
    def get_unfeatured_workflows(self, limit=5):
        """Get workflows that haven't been featured recently"""
        unfeatured = [w for w in self.workflows if not w.get('last_featured')]
        
        # Add workflows not featured in last 30 days
        thirty_days_ago = (datetime.now() - datetime.timedelta(days=30)).isoformat()
        recently_unfeatured = [w for w in self.workflows 
                             if w.get('last_featured') and w['last_featured'] < thirty_days_ago]
        
        all_candidates = unfeatured + recently_unfeatured
        
        # Sort by score
        return sorted(all_candidates, key=lambda x: x.get('showcase_score', 0), reverse=True)[:limit]
    
    def mark_as_featured(self, workflow_id):
        """Mark workflow as featured in latest report"""
        for workflow in self.workflows:
            if workflow['id'] == workflow_id:
                workflow['last_featured'] = datetime.now().isoformat()
                workflow['feature_count'] = workflow.get('feature_count', 0) + 1
                break
        self.save_database()
    
    def get_workflow_by_category(self):
        """Get workflows organized by category"""
        categories = {}
        
        for workflow in self.workflows:
            category = workflow.get('category', 'other')
            if category not in categories:
                categories[category] = []
            categories[category].append(workflow)
            
        return categories
    
    def search_workflows(self, query):
        """Search workflows by title, description, or apps"""
        query_lower = query.lower()
        results = []
        
        for workflow in self.workflows:
            searchable_text = (
                workflow.get('title', '') + ' ' +
                workflow.get('description', '') + ' ' +
                ' '.join(workflow.get('apps', []))
            ).lower()
            
            if query_lower in searchable_text:
                results.append(workflow)
                
        return sorted(results, key=lambda x: x.get('showcase_score', 0), reverse=True)
    
    def get_stats(self):
        """Get database statistics"""
        total = len(self.workflows)
        categories = {}
        apps = {}
        
        for workflow in self.workflows:
            # Count categories
            category = workflow.get('category', 'other')
            categories[category] = categories.get(category, 0) + 1
            
            # Count apps
            for app in workflow.get('apps', []):
                apps[app] = apps.get(app, 0) + 1
        
        return {
            'total_workflows': total,
            'categories': categories,
            'popular_apps': dict(sorted(apps.items(), key=lambda x: x[1], reverse=True)[:10]),
            'avg_apps_per_workflow': sum(len(w.get('apps', [])) for w in self.workflows) / max(total, 1)
        }

def populate_initial_database():
    """Populate database with curated workflows"""
    db = WorkflowDatabase()
    
    # Only add if database is empty
    if len(db.workflows) > 0:
        print(f"Database already has {len(db.workflows)} workflows")
        return db
    
    initial_workflows = [
        {
            'title': 'Competitor Price Monitor',
            'description': 'Automatically track competitor prices and alert when undercut',
            'apps': ['n8n', 'Web Scraper', 'Google Sheets', 'Slack'],
            'workflow': 'Scheduled trigger → Scrape competitor sites → Compare prices → Slack alert → Update sheet',
            'impact': 'Increased sales by 15%, saved 2 hours daily',
            'complexity': 'Intermediate',
            'time_to_build': '45 minutes',
            'category': 'e-commerce',
            'showcase_score': 9,
            'source': 'curated'
        },
        {
            'title': 'Smart Email-to-Task System',
            'description': 'AI analyzes emails and creates prioritized tasks automatically',
            'apps': ['Gmail', 'n8n', 'OpenAI', 'Notion', 'Slack'],
            'workflow': 'Gmail trigger → OpenAI analysis → Create Notion task → Assign team member → Slack notification',
            'impact': '0 missed requests, 70% faster response time',
            'complexity': 'Advanced',
            'time_to_build': '60 minutes', 
            'category': 'productivity',
            'showcase_score': 10,
            'source': 'curated'
        },
        {
            'title': 'Invoice Chase Bot',
            'description': 'Automatically chase overdue invoices with escalating reminders',
            'apps': ['QuickBooks', 'n8n', 'Twilio', 'SendGrid'],
            'workflow': 'Daily check → Day 1: email → Day 7: firm email → Day 14: SMS → Day 21: legal notice',
            'impact': 'Payment time reduced from 45 to 23 days, recovered $15K',
            'complexity': 'Intermediate',
            'time_to_build': '50 minutes',
            'category': 'finance',
            'showcase_score': 9,
            'source': 'curated'
        },
        {
            'title': 'Social Media Content Recycler',
            'description': 'Turn one post into content for all platforms automatically',
            'apps': ['n8n', 'Twitter API', 'LinkedIn API', 'ChatGPT', 'Buffer'],
            'workflow': 'Top post trigger → ChatGPT rewrite for each platform → Schedule everywhere → Track performance',
            'impact': '10x content output, 5 hours saved weekly',
            'complexity': 'Advanced',
            'time_to_build': '75 minutes',
            'category': 'marketing',
            'showcase_score': 8,
            'source': 'curated'
        },
        {
            'title': 'Apartment Hunting Bot',
            'description': 'Scrapes listings and sends only the perfect matches instantly',
            'apps': ['Python', 'BeautifulSoup', 'Telegram', 'Google Sheets'],
            'workflow': 'Scrape every 15 min → Filter criteria → Check blacklist → Telegram alert → Log to sheet',
            'impact': 'Found apartment 2 weeks faster than manual search',
            'complexity': 'Advanced',
            'time_to_build': '90 minutes',
            'category': 'personal',
            'showcase_score': 8,
            'source': 'reddit'
        }
    ]
    
    for workflow in initial_workflows:
        db.add_workflow(workflow)
        
    print(f"Added {len(initial_workflows)} workflows to database")
    return db

def main():
    print("🗄️  Workflow Database Manager")
    print("=" * 40)
    
    # Initialize database with curated workflows
    db = populate_initial_database()
    
    # Show stats
    stats = db.get_stats()
    print(f"\n📊 Database Stats:")
    print(f"   Total workflows: {stats['total_workflows']}")
    print(f"   Average apps per workflow: {stats['avg_apps_per_workflow']:.1f}")
    
    print(f"\n📂 Categories:")
    for category, count in stats['categories'].items():
        print(f"   {category}: {count}")
        
    print(f"\n🔥 Popular Apps:")
    for app, count in list(stats['popular_apps'].items())[:5]:
        print(f"   {app}: {count}")
    
    # Show best workflows
    print(f"\n🌟 Top 3 Workflows:")
    best = db.get_best_workflows(3)
    for i, workflow in enumerate(best, 1):
        print(f"\n{i}. {workflow['title']}")
        print(f"   🛠️  {' + '.join(workflow['apps'])}")
        print(f"   📊 {workflow['impact']}")
        print(f"   🎯 {workflow['complexity']} ({workflow['time_to_build']})")

if __name__ == "__main__":
    main()