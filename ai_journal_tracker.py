import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
from notion_client import Client
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class AIJournalTracker:
	def __init__(self):
		self.notion = Client(auth=os.getenv('NOTION_API_KEY'))
		self.database_id = os.getenv('NOTION_DATABASE_ID')
		self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
		self.analysis_model = os.getenv('ANALYSIS_MODEL', 'gpt-4o-mini')

		try:
			nltk.data.find('vader_lexicon')
		except LookupError:
			nltk.download('vader_lexicon')

		self.sentiment_analyzer = SentimentIntensityAnalyzer()

		self.mood_scores = {
			'Happy': 4, 'Excited': 4, 'Grateful': 4, 'Content': 3,
			'Neutral': 2, 'Calm': 3, 'Tired': 2, 'Anxious': 1,
			'Sad': 1, 'Stressed': 1, 'Frustrated': 1, 'Overwhelmed': 1
		}
		self.health_scores = {
			'Excellent': 5, 'Good': 4, 'Fair': 3, 'Poor': 2, 'Sick': 1
		}

	def fetch_journal_entries(self, days_back: int = 30) -> List[Dict[str, Any]]:
		try:
			start_date = (datetime.now() - timedelta(days=days_back)).isoformat()
			response = self.notion.databases.query(
				database_id=self.database_id,
				filter={ "property": "Date", "date": { "after": start_date } },
				sorts=[{ "property": "Date", "direction": "ascending" }]
			)
			entries = []
			for page in response.get('results', []):
				entry = self._parse_notion_page(page)
				if entry:
					entries.append(entry)
			return entries
		except Exception as e:
			print(f"Error fetching journal entries: {e}")
			return []

	def _parse_notion_page(self, page: Dict[str, Any]) -> Optional[Dict[str, Any]]:
		try:
			properties = page['properties']
			date_prop = properties.get('Date', {}).get('date')
			if not date_prop:
				return None
			entry_date = datetime.fromisoformat(date_prop['start'].replace('Z', '+00:00'))

			mood_prop = properties.get('Mood', {}).get('select')
			mood = mood_prop['name'] if mood_prop else 'Neutral'

			health_prop = properties.get('Health Status', {}).get('select')
			health = health_prop['name'] if health_prop else 'Fair'

			activities_prop = properties.get('Activities', {}).get('rich_text', [])
			activities = ' '.join([t['plain_text'] for t in activities_prop])

			notes_prop = properties.get('Notes', {}).get('rich_text', [])
			notes = ' '.join([t['plain_text'] for t in notes_prop])

			return {
				'date': entry_date,
				'mood': mood,
				'health': health,
				'activities': activities,
				'notes': notes,
				'page_id': page['id']
			}
		except Exception as e:
			print(f"Error parsing page: {e}")
			return None

	def analyze_mood_with_ai(self, entries: List[Dict[str, Any]]) -> Dict[str, Any]:
		if not entries:
			return {"error": "No entries to analyze"}
		recent = entries[-10:]
		prompt = self._create_analysis_prompt(recent)
		try:
			resp = self.openai_client.chat.completions.create(
				model=self.analysis_model,
				messages=[
					{ "role": "system", "content": "You are an AI wellness coach providing concise, actionable insights from journals." },
					{ "role": "user", "content": prompt }
				],
				max_tokens=500,
				temperature=0.7
			)
			ai_insights = resp.choices[0].message.content
			sentiment_scores = self._calculate_sentiment_scores(entries)
			trends = self._detect_trends(entries)
			return {
				"ai_insights": ai_insights,
				"sentiment_scores": sentiment_scores,
				"trends": trends,
				"analysis_date": datetime.now().isoformat()
			}
		except Exception as e:
			return {"error": f"AI analysis failed: {e}"}

	def _create_analysis_prompt(self, entries: List[Dict[str, Any]]) -> str:
		lines = ["Analyze these journal entries and provide insights:\n"]
		for e in entries:
			lines.append(f"Date: {e['date'].strftime('%Y-%m-%d')}")
			lines.append(f"Mood: {e['mood']}")
			lines.append(f"Health: {e['health']}")
			lines.append(f"Activities: {e['activities']}")
			lines.append(f"Notes: {e['notes']}\n")
		lines.append(
			"Please provide:\n"
			"1) Mood pattern analysis\n"
			"2) Health trend observations\n"
			"3) Activity-mood correlations\n"
			"4) 3 concrete recommendations\n"
			"5) Any concerning patterns"
		)
		return "\n".join(lines)

	def _calculate_sentiment_scores(self, entries: List[Dict[str, Any]]) -> Dict[str, float]:
		all_text = []
		mood_scores = []
		for e in entries:
			all_text.append(f"{e['activities']} {e['notes']}".strip())
			mood_scores.append(self.mood_scores.get(e['mood'], 2))
		sentiments = []
		for t in all_text:
			if t:
				s = self.sentiment_analyzer.polarity_scores(t)['compound']
				sentiments.append(s)
			else:
				sentiments.append(0.0)
		return {
			"average_sentiment": sum(sentiments)/len(sentiments) if sentiments else 0.0,
			"average_mood_score": sum(mood_scores)/len(mood_scores) if mood_scores else 0.0,
			"total_entries": len(entries)
		}

	def _detect_trends(self, entries: List[Dict[str, Any]]) -> Dict[str, Any]:
		if len(entries) < 3:
			return {"message": "Not enough data for trend analysis", "patterns": []}
		sorted_e = sorted(entries, key=lambda x: x['date'])
		moods = [self.mood_scores.get(e['mood'], 2) for e in sorted_e]
		healths = [self.health_scores.get(e['health'], 3) for e in sorted_e]
		mood_trend = self._slope(moods)
		health_trend = self._slope(healths)
		patterns = self._find_patterns(sorted_e)
		return {
			"mood_trend": "improving" if mood_trend > 0.1 else "declining" if mood_trend < -0.1 else "stable",
			"health_trend": "improving" if health_trend > 0.1 else "declining" if health_trend < -0.1 else "stable",
			"mood_trend_score": mood_trend,
			"health_trend_score": health_trend,
			"patterns": patterns
		}

	def _slope(self, y: List[float]) -> float:
		n = len(y)
		if n < 2:
			return 0.0
		x = list(range(n))
		sum_x = sum(x)
		sum_y = sum(y)
		sum_xy = sum(x[i]*y[i] for i in range(n))
		sum_x2 = sum(v*v for v in x)
		den = (n*sum_x2 - sum_x*sum_x)
		return (n*sum_xy - sum_x*sum_y)/den if den != 0 else 0.0

	def _find_patterns(self, entries: List[Dict[str, Any]]) -> List[str]:
		p = []
		wend, wkdy = [], []
		for e in entries:
			score = self.mood_scores.get(e['mood'], 2)
			if e['date'].weekday() >= 5:
				wend.append(score)
			else:
				wkdy.append(score)
		if wend and wkdy:
			aw = sum(wend)/len(wend)
			ad = sum(wkdy)/len(wkdy)
			if aw > ad + 0.5:
				p.append("Higher mood on weekends.")
			elif ad > aw + 0.5:
				p.append("Higher mood on weekdays.")
		p.extend(self._activity_corr(entries))
		return p

	def _activity_corr(self, entries: List[Dict[str, Any]]) -> List[str]:
		keywords = ['exercise', 'workout', 'walk', 'run', 'yoga', 'meditation', 'work', 'meeting', 'social', 'friend']
		bucket: Dict[str, List[float]] = {}
		for e in entries:
			a = e['activities'].lower()
			score = self.mood_scores.get(e['mood'], 2)
			for k in keywords:
				if k in a:
					bucket.setdefault(k, []).append(score)
		out = []
		for k, arr in bucket.items():
			if len(arr) >= 2:
				avg = sum(arr)/len(arr)
				if avg > 3:
					out.append(f"'{k}' tends to boost mood.")
				elif avg < 2:
					out.append(f"'{k}' tends to lower mood.")
		return out

	def create_visualizations(self, entries: List[Dict[str, Any]], analysis: Dict[str, Any]):
		if not entries:
			print("No entries to visualize")
			return
		sorted_e = sorted(entries, key=lambda x: x['date'])
		dates = [e['date'] for e in sorted_e]
		moods = [self.mood_scores.get(e['mood'], 2) for e in sorted_e]
		healths = [self.health_scores.get(e['health'], 3) for e in sorted_e]

		fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 10))
		ax1.plot(dates, moods, marker='o', linewidth=2, color='#FF6B6B')
		ax1.set_title('Mood Trends Over Time'); ax1.set_ylabel('Mood Score'); ax1.grid(True, alpha=0.3); ax1.set_ylim(0, 5)
		mood_labels = {v: k for k, v in self.mood_scores.items()}
		ax1.set_yticks(sorted(set(mood_labels.keys())))
		ax1.set_yticklabels([mood_labels[s] for s in sorted(set(mood_labels.keys()))])

		ax2.plot(dates, healths, marker='s', linewidth=2, color='#4ECDC4')
		ax2.set_title('Health Status Trends Over Time'); ax2.set_ylabel('Health Score'); ax2.grid(True, alpha=0.3); ax2.set_ylim(0, 6)
		health_labels = {v: k for k, v in self.health_scores.items()}
		ax2.set_yticks(sorted(set(health_labels.keys())))
		ax2.set_yticklabels([health_labels[s] for s in sorted(set(health_labels.keys()))])

		ax3.plot(dates, moods, marker='o', linewidth=2, color='#FF6B6B', label='Mood')
		ax3.plot(dates, healths, marker='s', linewidth=2, color='#4ECDC4', label='Health')
		ax3.set_title('Combined Mood & Health Trends'); ax3.set_ylabel('Score'); ax3.set_xlabel('Date'); ax3.legend(); ax3.grid(True, alpha=0.3)

		for ax in (ax1, ax2, ax3):
			ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
			ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(dates)//10)))
			plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)

		plt.tight_layout()
		plt.savefig('mood_health_trends.png', dpi=300, bbox_inches='tight')
		print("Saved: mood_health_trends.png")

	def generate_report(self, entries: List[Dict[str, Any]], analysis: Dict[str, Any]) -> str:
		if not entries:
			return "No journal entries found."
		start = min(e['date'] for e in entries).strftime('%Y-%m-%d')
		end = max(e['date'] for e in entries).strftime('%Y-%m-%d')
		sent = analysis.get('sentiment_scores', {})
		tr = analysis.get('trends', {})
		report = []
		report.append(f"AI Wellness Journal Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
		report.append(f"Entries analyzed: {len(entries)} (Range: {start} to {end})")
		report.append("")
		report.append("AI Insights:")
		report.append(analysis.get('ai_insights', 'No AI insights'))
		report.append("")
		report.append(f"Average sentiment: {sent.get('average_sentiment', 0):.2f}")
		report.append(f"Average mood score: {sent.get('average_mood_score', 0):.2f}")
		report.append(f"Mood trend: {tr.get('mood_trend', 'Unknown')} ({tr.get('mood_trend_score', 0):.2f})")
		report.append(f"Health trend: {tr.get('health_trend', 'Unknown')} ({tr.get('health_trend_score', 0):.2f})")
		report.append("Patterns:")
		for p in tr.get('patterns', []) or ["None detected"]:
			report.append(f"- {p}")
		return "\n".join(report)

	def run_analysis(self, days_back: int = 30, save_report: bool = True):
		print("Fetching journal entries...")
		entries = self.fetch_journal_entries(days_back)
		if not entries:
			print("No journal entries found.")
			return
		print("Analyzing with AI...")
		analysis = self.analyze_mood_with_ai(entries)
		print("Creating visualizations...")
		self.create_visualizations(entries, analysis)
		print("Generating report...")
		report = self.generate_report(entries, analysis)
		if save_report:
			with open('wellness_report.txt', 'w', encoding='utf-8') as f:
				f.write(report)
			print("Saved: wellness_report.txt")
		return { 'entries': entries, 'analysis': analysis, 'report': report }

def main():
	print("AI Notion Journal Tracker")
	req = ['NOTION_API_KEY', 'NOTION_DATABASE_ID', 'OPENAI_API_KEY']
	miss = [v for v in req if not os.getenv(v)]
	if miss:
		print(f"Missing env vars: {', '.join(miss)}")
		return
	tracker = AIJournalTracker()
	try:
		tracker.run_analysis(days_back=30)
		print("Done.")
	except Exception as e:
		print(f"Error: {e}")

if __name__ == "__main__":
	main()
