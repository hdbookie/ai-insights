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
            msg = MIMEMultipart()
            msg['From'] = self.email_user
            msg['To'] = self.recipient_email
            msg['Subject'] = f"AI Trends Daily Report - {datetime.now().strftime('%Y-%m-%d')}"
            
            body = f"""
AI Trends & Best Practices Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
Posts Analyzed: {post_count}

{analysis}

---
Powered by Gemini AI Feed Analyzer
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
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
