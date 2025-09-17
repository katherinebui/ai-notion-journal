import os
from dotenv import load_dotenv

def check_requirements():
	try:
		import notion_client, openai, nltk, matplotlib, pandas  # noqa
		print("Dependencies OK")
		return True
	except ImportError as e:
		print(f"Missing package: {e}. Run: pip install -r requirements.txt")
		return False

def download_nltk():
	try:
		import nltk
		nltk.download('vader_lexicon', quiet=True)
		print("NLTK data OK")
		return True
	except Exception as e:
		print(f"NLTK error: {e}")
		return False

def check_env():
	load_dotenv()
	req = ['NOTION_API_KEY', 'NOTION_DATABASE_ID', 'OPENAI_API_KEY']
	miss = [v for v in req if not os.getenv(v)]
	if miss:
		print(f"Missing env: {', '.join(miss)}")
		return False
	print("Env OK")
	return True

def main():
	print("AI Notion Journal - Quick Start")
	if not check_requirements(): return
	if not download_nltk(): return
	if not check_env():
		print("Copy .env.example to .env and fill values.")
		return
	from ai_journal_tracker import AIJournalTracker
	AIJournalTracker().run_analysis(days_back=30)
	print("All set.")

if __name__ == "__main__":
	main()
