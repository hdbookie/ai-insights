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

# Load environment variables from .env file
load_dotenv()

class AIFeedAnalyzer:
    def __init__(self):
        self.feeds = [
            "https://www.reddit.com/r/MachineLearning/hot.rss",
            "https://www.reddit.com/r/artificial/hot.rss", 
            "https://www.reddit.com/r/OpenAI/hot.rss",
            "https://www.reddit.com/r/ClaudeAI/hot.rss",
            "https://www.reddit.com/r/LocalLLaMA/hot.rss",
            "https://www.reddit.com/r/n8n/hot.rss",
            "https://www.reddit.com/r/automation/hot.rss",
            "https://www.reddit.com/r/nocode/hot.rss",
            "https://news.ycombinator.com/rss",
            "https://www.producthunt.com/topics/artificial-intelligence.rss"
        ]
        
        # You'll need to set these environment variables
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')
        self.email_user = os.getenv('EMAIL_USER')
        self.email_pass = os.getenv('EMAIL_PASS')
        self.recipient_email = os.getenv('RECIPIENT_EMAIL')
        
    def fetch_recent_posts(self, hours_back: int = 24) -> List[Dict]:
        """Fetch posts from the last N hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        all_posts = []
        
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
                        post = {
                            'title': entry.title,
                            'link': entry.link,
                            'summary': getattr(entry, 'summary', ''),
                            'published': pub_date.isoformat(),
                            'source': feed.feed.title if hasattr(feed.feed, 'title') else feed_url
                        }
                        all_posts.append(post)
                        
                time.sleep(1)  # Be nice to the servers
                
            except Exception as e:
                print(f"Error fetching {feed_url}: {e}")
                continue
                
        return all_posts
    
    def analyze_with_gemini(self, posts: List[Dict]) -> str:
        """Send posts to Gemini for analysis"""
        if not self.gemini_api_key:
            return "Error: GEMINI_API_KEY not set"
            
        # Prepare content for Gemini
        prompt = "Analyze these recent AI/automation posts and extract:\n"
        prompt += "1. Key trends and emerging tools\n"
        prompt += "2. Best practices and workflows mentioned\n"
        prompt += "3. Notable new releases or breakthroughs\n"
        prompt += "4. Practical tips and use cases\n\n"
        prompt += "Format as a clear, actionable summary with bullet points.\n\n"
        
        for post in posts[:40]:  # Gemini has higher token limits
            prompt += f"Title: {post['title']}\n"
            prompt += f"Source: {post['source']}\n"
            prompt += f"Summary: {post['summary'][:300]}...\n"
            prompt += f"Link: {post['link']}\n\n"
        
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
            
            # Convert markdown-style formatting to HTML
            html_analysis = analysis.replace('\n', '<br>')
            html_analysis = html_analysis.replace('**', '</b>').replace('</b>', '<b>', 1)
            html_analysis = html_analysis.replace('* ', '<li>')
            html_analysis = html_analysis.replace('##', '</h2>').replace('</h2>', '<h2>', 1)
            
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
            <h1>🤖 AI Trends & Best Practices Report</h1>
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
            <p>This report analyzes the latest AI and automation trends from Reddit, Hacker News, and Product Hunt</p>
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
