# AI Insights - Daily Feed Analyzer

Automatically monitors AI/automation RSS feeds and generates intelligent daily summaries using Gemini AI.

## What it does

- Monitors RSS feeds from Reddit (MachineLearning, OpenAI, ClaudeAI, etc.), Hacker News, and Product Hunt
- Fetches posts from the last 24 hours
- Uses Gemini AI to analyze content and extract:
  - Key trends and emerging tools
  - Best practices and workflows
  - Notable releases and breakthroughs  
  - Practical tips and use cases
- Emails you a daily digest every morning

## Setup

### 1. Get API Keys

- **Gemini API Key**: Get free key at https://aistudio.google.com/app/apikey
- **Gmail App Password**: Enable 2FA on Gmail, then generate app password in security settings

### 2. Configure GitHub Secrets

In your GitHub repo settings → Secrets and variables → Actions, add:

- `GEMINI_API_KEY` - Your Gemini API key
- `EMAIL_USER` - Your Gmail address  
- `EMAIL_PASS` - Your Gmail app password
- `RECIPIENT_EMAIL` - Where to send the daily report

### 3. Schedule

The workflow runs automatically every day at 8 AM UTC. You can also trigger it manually from the Actions tab.

## Cost

Very cheap! Gemini Flash costs ~$0.01-0.02 per day for this analysis.

## Files

- `ai_feed_analyzer.py` - Main Python script
- `.github/workflows/daily-analysis.yml` - GitHub Actions workflow
- `README.md` - This file

## Testing

1. Push to GitHub
2. Go to Actions tab
3. Click "Run workflow" to test manually
4. Check logs to verify everything works

Enjoy your daily AI insights! 🤖
