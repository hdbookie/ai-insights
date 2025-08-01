#!/usr/bin/env python3
"""
AI Feed Analyzer - Monitors RSS feeds and generates intelligent summaries
"""

import feedparser
import requests
import json
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from typing import List, Dict
import time
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import re

# Import our new workflow discovery modules
from scrape_make_templates import MakeTemplateScraper
from fetch_n8n_workflows import N8nWorkflowFetcher
from reddit_showcase_monitor import RedditShowcaseMonitor
from workflow_database import WorkflowDatabase

# Load environment variables from .env file
load_dotenv()

class AIFeedAnalyzer:
    def __init__(self):
        self.feeds = [
            # n8n Community - Workflows & Showcases
            "https://community.n8n.io/c/workflows/8.rss",
            "https://community.n8n.io/c/show/12.rss",
            "https://community.n8n.io/c/questions/6.rss",  # Often contain workflow examples
            
            # Reddit Automation Communities
            "https://www.reddit.com/r/automation/.rss",
            "https://www.reddit.com/r/n8n/.rss",
            "https://www.reddit.com/r/nocode/.rss",
            
            # Dev.to specific tags
            "https://dev.to/feed/tag/showdev",
            "https://dev.to/feed/tag/automation",
            "https://dev.to/feed/tag/workflow",
            
            # Workflow blogs
            "https://blog.n8n.io/rss/",
            "https://www.make.com/en/blog/feed",
            "https://zapier.com/blog/feeds/latest/",
        ]
        
        # You'll need to set these environment variables
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')
        self.email_user = os.getenv('EMAIL_USER')
        self.email_pass = os.getenv('EMAIL_PASS')
        self.recipient_email = os.getenv('RECIPIENT_EMAIL')
        
        # Initialize workflow discovery tools
        self.make_scraper = MakeTemplateScraper()
        self.n8n_fetcher = N8nWorkflowFetcher()
        self.reddit_monitor = RedditShowcaseMonitor()
        self.workflow_db = WorkflowDatabase()
        
    def fetch_recent_posts(self, hours_back: int = 24) -> List[Dict]:
        """Fetch posts from the last N hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        all_posts = []
        
        # Keywords to prioritize automation content
        automation_keywords = [
            'n8n', 'make.com', 'zapier', 'activepieces', 'langchain', 'claude',
            'workflow', 'automation', 'integration', 'no-code', 'low-code',
            'api', 'webhook', 'trigger', 'template', 'tutorial', 'rss to',
            'automate', 'connect', 'sync', 'pipeline', 'orchestration',
            'built', 'created', 'saved hours', 'reduced time', 'showcase',
            'example', 'case study', 'how i', 'guide', 'step-by-step'
        ]
        
        # Keywords that indicate concrete examples
        showcase_keywords = [
            'built', 'created', 'made', 'developed', 'launched',
            'saved', 'reduced', 'improved', 'automated',
            'tutorial', 'guide', 'example', 'showcase', 'demo'
        ]
        
        for feed_url in self.feeds:
            try:
                print(f"Fetching from {feed_url}")
                feed = feedparser.parse(feed_url)
                
                for entry in feed.entries:
                    # Parse publication date
                    pub_date = None
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        pub_date = datetime(*entry.published_parsed[:6])
                    
                    # Only include recent posts
                    if pub_date and pub_date > cutoff_time:
                        title_lower = entry.title.lower()
                        summary_lower = getattr(entry, 'summary', '').lower()
                        
                        # Calculate relevance score
                        relevance_score = sum(
                            1 for keyword in automation_keywords 
                            if keyword in title_lower or keyword in summary_lower
                        )
                        
                        # Bonus points for concrete examples
                        showcase_score = sum(
                            2 for keyword in showcase_keywords
                            if keyword in title_lower
                        )
                        
                        # Extract potential metrics
                        import re
                        time_saved = re.findall(r'(\d+)\s*(?:hours?|minutes?|days?)\s*(?:saved|reduced)', 
                                              title_lower + ' ' + summary_lower)
                        percentage_improved = re.findall(r'(\d+)%\s*(?:improvement|reduction|faster|increase)', 
                                                       title_lower + ' ' + summary_lower)
                        
                        post = {
                            'title': entry.title,
                            'link': entry.link,
                            'summary': getattr(entry, 'summary', ''),
                            'published': pub_date.isoformat(),
                            'source': feed.feed.title if hasattr(feed.feed, 'title') else feed_url,
                            'relevance_score': relevance_score + showcase_score,
                            'is_showcase': showcase_score > 0,
                            'metrics': {
                                'time_saved': time_saved,
                                'percentage': percentage_improved
                            }
                        }
                        all_posts.append(post)
                        
                time.sleep(1)  # Be nice to the servers
                
            except Exception as e:
                print(f"Error fetching {feed_url}: {e}")
                continue
        
        # Sort by relevance score and date
        all_posts.sort(key=lambda x: (x['relevance_score'], x['published']), reverse=True)
        
        return all_posts
    
    def fetch_full_content(self, url: str) -> Dict[str, str]:
        """Fetch full content from a URL"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Try to find the main content area
            content = None
            
            # Common content selectors
            selectors = [
                'article', 
                'main',
                '[role="main"]',
                '.post-content',
                '.entry-content',
                '.content',
                '#content',
                '.article-body',
                '.post-body'
            ]
            
            for selector in selectors:
                element = soup.select_one(selector)
                if element:
                    content = element.get_text(separator=' ', strip=True)
                    break
            
            # Fallback to body
            if not content:
                content = soup.get_text(separator=' ', strip=True)
            
            # Extract workflow-specific details
            workflow_details = {
                'full_text': content[:5000],  # First 5000 chars
                'code_blocks': [],
                'metrics': [],
                'workflow_steps': []
            }
            
            # Find code blocks and JSON configs
            code_elements = soup.find_all(['pre', 'code'])
            for code in code_elements[:3]:  # Max 3 code blocks
                code_text = code.get_text(strip=True)
                workflow_details['code_blocks'].append(code_text[:500])
                
                # Check if it's a workflow JSON
                if '{' in code_text and ('nodes' in code_text or 'trigger' in code_text):
                    workflow_details['workflow_steps'].append("Found workflow configuration")
            
            # Look for step-by-step instructions
            step_patterns = [
                r'(?:step\s*\d+|first|then|next|finally)[\s:]+([^.]+)',
                r'(?:\d+\.|•|→)\s*([^.\n]+)',
                r'(?:trigger|action|filter):\s*([^.\n]+)'
            ]
            
            for pattern in step_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                workflow_details['workflow_steps'].extend(matches[:5])
            
            # Extract metrics
            metrics_patterns = [
                r'(\d+)\s*(?:hours?|minutes?|days?)\s*(?:saved|reduced)',
                r'(\d+)%\s*(?:improvement|reduction|faster|increase)',
                r'(\d+x)\s*(?:faster|improvement)',
                r'saved\s*\$(\d+)',
                r'reduced\s*(?:by\s*)?(\d+)%'
            ]
            
            for pattern in metrics_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                workflow_details['metrics'].extend(matches)
            
            return workflow_details
            
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return {'full_text': '', 'code_blocks': [], 'metrics': []}
    
    def discover_new_workflows(self):
        """Discover new workflows from all sources"""
        print("🔍 Discovering new workflows from all sources...")
        new_workflows = []
        
        try:
            # Get Make.com templates
            print("  Checking Make.com templates...")
            make_templates = self.make_scraper.get_templates(limit=3)
            for template in make_templates:
                if template.get('description'):
                    workflow = {
                        'title': template['title'],
                        'description': template['description'],
                        'apps': template.get('apps', []),
                        'source': 'Make.com',
                        'url': template.get('url', ''),
                        'showcase_score': 6
                    }
                    new_workflows.append(workflow)
        except:
            pass
            
        try:
            # Get n8n community examples
            print("  Checking n8n workflows...")
            n8n_examples = self.n8n_fetcher.get_workflow_examples()
            for example in n8n_examples[:2]:  # Top 2
                workflow = {
                    'title': example['title'],
                    'description': example['description'], 
                    'apps': example['apps'],
                    'workflow': example['workflow'],
                    'impact': example['impact'],
                    'complexity': example['complexity'],
                    'time_to_build': example['time_to_build'],
                    'source': 'n8n Examples',
                    'showcase_score': 8
                }
                new_workflows.append(workflow)
        except:
            pass
            
        try:
            # Get Reddit showcases
            print("  Checking Reddit showcases...")
            reddit_showcases = self.reddit_monitor.get_curated_showcases()
            for showcase in reddit_showcases[:2]:  # Top 2
                workflow = {
                    'title': showcase['title'],
                    'description': showcase['description'],
                    'apps': showcase['apps'],
                    'workflow': showcase['workflow'], 
                    'impact': showcase['impact'],
                    'complexity': showcase['complexity'],
                    'source': 'Reddit Community',
                    'showcase_score': 9
                }
                new_workflows.append(workflow)
        except:
            pass
        
        return new_workflows
    
    def analyze_with_gemini(self, posts: List[Dict]) -> str:
        """Send posts to Gemini for analysis"""
        if not self.gemini_api_key:
            return "Error: GEMINI_API_KEY not set"
            
        # Discover new workflows from all sources
        new_workflows = self.discover_new_workflows()
        
        # Get best workflows from database
        db_workflows = self.workflow_db.get_best_workflows(5)
        
        # Create deep dive report
        prompt = "Create a 'Weekly Workflow Deep Dive' report focused on AMAZING automation workflows.\n\n"
        
        prompt += "Format EXACTLY like this:\n\n"
        
        prompt += "# 🏆 WORKFLOW OF THE WEEK\n\n"
        prompt += "**[Pick most impressive workflow]** - [One sentence impact]\n\n"
        prompt += "**The Problem:** [Specific problem this solves]\n\n"
        prompt += "**The Solution:**\n"
        prompt += "[Step 1] → [Step 2] → [Step 3] → [Result]\n\n"
        prompt += "**Tools Needed:** [Tool 1] + [Tool 2] + [Tool 3]\n"
        prompt += "**Time to Build:** [X minutes]\n"
        prompt += "**Impact:** [Specific results]\n"
        prompt += "**Why It's Cool:** [What makes it clever]\n\n"
        
        prompt += "# 🚀 THIS WEEK'S COOLEST BUILDS\n\n"
        prompt += "## [Workflow Name 1]\n"
        prompt += "- **Problem:** [What it solves]\n"
        prompt += "- **Flow:** [Simple workflow]\n"
        prompt += "- **Tools:** [List of tools]\n"
        prompt += "- **Result:** [Impact with numbers]\n\n"
        
        prompt += "## [Workflow Name 2]\n"
        prompt += "- **Problem:** [What it solves]\n"
        prompt += "- **Flow:** [Simple workflow]\n"
        prompt += "- **Tools:** [List of tools]\n"
        prompt += "- **Result:** [Impact with numbers]\n\n"
        
        prompt += "# 💰 MONEY MAKERS\n\n"
        prompt += "Workflows that directly generate or save money:\n"
        prompt += "- **[Name 1]**: [How it makes/saves money]\n"
        prompt += "- **[Name 2]**: [How it makes/saves money]\n\n"
        
        prompt += "# ⚡ 15-MINUTE QUICK WINS\n\n"
        prompt += "Simple automations anyone can build today:\n"
        prompt += "- **[Name 1]**: [What it does] - [Tools needed]\n"
        prompt += "- **[Name 2]**: [What it does] - [Tools needed]\n\n"
        
        prompt += "# 🔥 TRENDING TOOLS\n\n"
        prompt += "- **[Tool 1]**: [Why it's popular]\n"
        prompt += "- **[Tool 2]**: [Why it's popular]\n\n"
        
        prompt += "Here are amazing workflows to choose from:\n\n"
        
        # Add database workflows
        prompt += "**FROM DATABASE:**\n"
        for workflow in db_workflows:
            prompt += f"- **{workflow['title']}**: {workflow.get('description', '')} | "
            prompt += f"Tools: {' + '.join(workflow.get('apps', []))} | "
            prompt += f"Impact: {workflow.get('impact', 'High value')} | "
            prompt += f"Time: {workflow.get('time_to_build', 'Unknown')}\n"
        
        # Add discovered workflows
        if new_workflows:
            prompt += "\n**NEWLY DISCOVERED:**\n"
            for workflow in new_workflows:
                prompt += f"- **{workflow['title']}**: {workflow.get('description', '')} | "
                prompt += f"Tools: {' + '.join(workflow.get('apps', []))} | "
                prompt += f"Source: {workflow.get('source', '')}\n"
        
        prompt += "\nPick the BEST workflows and create an amazing deep dive report!\n\n"
        
        # Prioritize showcase posts
        showcase_posts = [p for p in posts if p.get('is_showcase', False)]
        other_posts = [p for p in posts if not p.get('is_showcase', False)]
        
        # Analyze showcase posts first, then others
        all_sorted = showcase_posts[:20] + other_posts[:20]
        
        # Fetch full content for top 10 most promising posts
        print("Fetching full content for top posts...")
        for i, post in enumerate(all_sorted[:10]):
            print(f"  Fetching {i+1}/10: {post['title'][:50]}...")
            full_content = self.fetch_full_content(post['link'])
            post['full_content'] = full_content
            time.sleep(1)  # Be nice to servers
        
        for post in all_sorted[:40]:  # Gemini has higher token limits
            prompt += f"Title: {post['title']}\n"
            prompt += f"Source: {post['source']}\n"
            prompt += f"Link: {post['link']}\n"
            
            # Include full content if available
            if post.get('full_content') and post['full_content']['full_text']:
                prompt += f"FULL ARTICLE CONTENT:\n{post['full_content']['full_text'][:2000]}\n"
                
                if post['full_content']['code_blocks']:
                    prompt += f"CODE EXAMPLES:\n"
                    for code in post['full_content']['code_blocks'][:2]:
                        prompt += f"```\n{code}\n```\n"
                
                if post['full_content']['metrics']:
                    prompt += f"METRICS FOUND: {', '.join(post['full_content']['metrics'])}\n"
                
                if post['full_content']['workflow_steps']:
                    prompt += f"WORKFLOW STEPS FOUND:\n"
                    for step in post['full_content']['workflow_steps'][:5]:
                        prompt += f"  - {step}\n"
            else:
                prompt += f"Summary: {post['summary'][:300]}...\n"
                if post.get('metrics', {}).get('time_saved'):
                    prompt += f"Time Saved: {', '.join(post['metrics']['time_saved'])}\n"
                if post.get('metrics', {}).get('percentage'):
                    prompt += f"Improvement: {', '.join(post['metrics']['percentage'])}%\n"
            
            prompt += "\n"
        
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.gemini_api_key}"
            
            data = {
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }],
                "generationConfig": {
                    "temperature": 0.3,
                    "topK": 40,
                    "topP": 0.95,
                    "maxOutputTokens": 2048,
                }
            }
            
            response = requests.post(url, json=data)
            
            if response.status_code == 200:
                result = response.json()
                if 'candidates' in result and len(result['candidates']) > 0:
                    return result['candidates'][0]['content']['parts'][0]['text']
                else:
                    return "No response generated from Gemini"
            else:
                return f"Error calling Gemini API: {response.status_code} - {response.text}"
                
        except Exception as e:
            return f"Error analyzing with Gemini: {e}"
    
    def send_email_report(self, analysis: str, post_count: int):
        """Send the daily report via email"""
        if not all([self.email_user, self.email_pass, self.recipient_email]):
            print("Email credentials not set - printing report instead:")
            print("="*50)
            print(analysis)
            print("="*50)
            return
            
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = self.email_user
            msg['To'] = self.recipient_email
            msg['Subject'] = f"🤖 AI Trends Daily Report - {datetime.now().strftime('%B %d, %Y')}"
            
            # Enhanced HTML conversion for better formatting
            html_analysis = analysis
            
            # Convert headers
            import re
            html_analysis = re.sub(r'\*\*(\d+\..+?)\*\*', r'<h3>\1</h3>', html_analysis)
            html_analysis = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html_analysis)
            
            # Convert bullet points with proper indentation
            lines = html_analysis.split('\n')
            formatted_lines = []
            in_list = False
            
            for line in lines:
                if line.strip().startswith('- '):
                    if not in_list:
                        formatted_lines.append('<ul>')
                        in_list = True
                    formatted_lines.append(f'<li>{line.strip()[2:]}</li>')
                else:
                    if in_list and not line.strip().startswith('  '):
                        formatted_lines.append('</ul>')
                        in_list = False
                    if line.strip():
                        formatted_lines.append(f'{line}<br>')
                    else:
                        formatted_lines.append('<br>')
            
            if in_list:
                formatted_lines.append('</ul>')
            
            html_analysis = '\n'.join(formatted_lines)
            
            # HTML body
            html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 700px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            background-color: white;
            border-radius: 10px;
            padding: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            border-bottom: 3px solid #4285f4;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        .header h1 {{
            color: #4285f4;
            margin: 0;
            font-size: 28px;
        }}
        .meta {{
            color: #666;
            font-size: 14px;
            margin-top: 10px;
        }}
        .stats {{
            background-color: #f8f9fa;
            border-radius: 8px;
            padding: 15px;
            margin: 20px 0;
            text-align: center;
        }}
        .stats-item {{
            display: inline-block;
            margin: 0 20px;
        }}
        .stats-number {{
            font-size: 24px;
            font-weight: bold;
            color: #4285f4;
        }}
        .stats-label {{
            font-size: 12px;
            color: #666;
            text-transform: uppercase;
        }}
        h2 {{
            color: #2c3e50;
            border-bottom: 2px solid #ecf0f1;
            padding-bottom: 10px;
            margin-top: 30px;
        }}
        h3 {{
            color: #34495e;
            margin-top: 20px;
            background-color: #f0f4f8;
            padding: 10px 15px;
            border-radius: 5px;
            border-left: 4px solid #4285f4;
        }}
        ul {{
            list-style: none;
            padding-left: 0;
        }}
        li {{
            position: relative;
            padding-left: 25px;
            margin-bottom: 12px;
            line-height: 1.8;
        }}
        li:before {{
            content: "▸";
            position: absolute;
            left: 0;
            color: #4285f4;
            font-weight: bold;
        }}
        b {{
            color: #2c3e50;
        }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ecf0f1;
            color: #7f8c8d;
            font-size: 12px;
        }}
        .note {{
            background-color: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
        }}
        .note strong {{
            color: #856404;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Automation Workflows & AI Intelligence Report</h1>
            <div class="meta">
                {datetime.now().strftime('%A, %B %d, %Y at %I:%M %p')}
            </div>
        </div>
        
        <div class="stats">
            <div class="stats-item">
                <div class="stats-number">{post_count}</div>
                <div class="stats-label">Posts Analyzed</div>
            </div>
            <div class="stats-item">
                <div class="stats-number">{len(self.feeds)}</div>
                <div class="stats-label">Sources Monitored</div>
            </div>
            <div class="stats-item">
                <div class="stats-number">24h</div>
                <div class="stats-label">Time Period</div>
            </div>
        </div>
        
        <div class="content">
            {html_analysis}
        </div>
        
        <div class="footer">
            <p>Powered by Gemini AI Feed Analyzer</p>
            <p>Monitoring automation platforms: n8n • Make.com • Zapier • ActivePieces • LangChain</p>
            <p>Curating the best workflows, templates, and integration ideas from the automation community</p>
        </div>
    </div>
</body>
</html>
            """
            
            # Plain text fallback
            plain_body = f"""
AI Trends & Best Practices Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
Posts Analyzed: {post_count}

{analysis}

---
Powered by Gemini AI Feed Analyzer
            """
            
            # Attach both versions
            msg.attach(MIMEText(plain_body, 'plain'))
            msg.attach(MIMEText(html_body, 'html'))
            
            # Connect to Gmail SMTP
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(self.email_user, self.email_pass)
            
            text = msg.as_string()
            server.sendmail(self.email_user, self.recipient_email, text)
            server.quit()
            
            print("Report sent successfully!")
            
        except Exception as e:
            print(f"Error sending email: {e}")
    
    def run_daily_analysis(self):
        """Main function to run the daily analysis"""
        print(f"Starting AI feed analysis at {datetime.now()}")
        
        # Fetch recent posts
        posts = self.fetch_recent_posts(24)
        print(f"Found {len(posts)} recent posts")
        
        if not posts:
            print("No recent posts found")
            return
        
        # Analyze with Gemini
        print("Analyzing posts with Gemini...")
        analysis = self.analyze_with_gemini(posts)
        
        # Send report
        self.send_email_report(analysis, len(posts))
        
        print("Analysis complete!")

def main():
    analyzer = AIFeedAnalyzer()
    analyzer.run_daily_analysis()

if __name__ == "__main__":
    main()
