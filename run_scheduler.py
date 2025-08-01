#!/usr/bin/env python3
"""Run AI Feed Analyzer on a schedule"""

import schedule
import time
from datetime import datetime
from ai_feed_analyzer import AIFeedAnalyzer

def run_analysis():
    print(f"Running scheduled analysis at {datetime.now()}")
    analyzer = AIFeedAnalyzer()
    analyzer.run_daily_analysis()

# Schedule options - uncomment the one you want:

# Daily at 9 AM
schedule.every().day.at("09:00").do(run_analysis)

# Every 6 hours
# schedule.every(6).hours.do(run_analysis)

# Every weekday at 8 AM
# schedule.every().monday.at("08:00").do(run_analysis)
# schedule.every().tuesday.at("08:00").do(run_analysis)
# schedule.every().wednesday.at("08:00").do(run_analysis)
# schedule.every().thursday.at("08:00").do(run_analysis)
# schedule.every().friday.at("08:00").do(run_analysis)

print("🤖 AI Feed Analyzer Scheduler Started")
print(f"Next run scheduled for: {schedule.next_run()}")

while True:
    schedule.run_pending()
    time.sleep(60)  # Check every minute