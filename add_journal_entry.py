import os
from datetime import datetime
from notion_client import Client
from dotenv import load_dotenv

load_dotenv()

class JournalEntryAdder:
	def __init__(self):
		self.notion = Client(auth=os.getenv('NOTION_API_KEY'))
		self.database_id = os.getenv('NOTION_DATABASE_ID')
		self.mood_options = ["Happy","Excited","Grateful","Content","Neutral","Calm","Tired","Anxious","Sad","Stressed","Frustrated","Overwhelmed"]
		self.health_options = ["Excellent","Good","Fair","Poor","Sick"]

	def add_entry(self):
		print("Add Journal Entry")
		title = input("Title: ").strip() or f"Journal Entry - {datetime.now().strftime('%Y-%m-%d')}"
		date_str = input(f"Date (YYYY-MM-DD) [default {datetime.now().strftime('%Y-%m-%d')}]: ").strip() or datetime.now().strftime('%Y-%m-%d')
		print("Mood options:", ", ".join(self.mood_options))
		mood = input("Mood: ").strip() or "Neutral"
		if mood not in self.mood_options:
			mood = "Neutral"
		print("Health options:", ", ".join(self.health_options))
		health = input("Health Status: ").strip() or "Fair"
		if health not in self.health_options:
			health = "Fair"
		activities = input("Activities: ").strip()
		notes = input("Notes: ").strip()

		props = {
			"Title": {"title": [{"text": {"content": title}}]},
			"Date": {"date": {"start": date_str}},
			"Mood": {"select": {"name": mood}},
			"Health Status": {"select": {"name": health}},
			"Activities": {"rich_text": [{"text": {"content": activities}}]},
			"Notes": {"rich_text": [{"text": {"content": notes}}]}
		}
		resp = self.notion.pages.create(parent={"database_id": self.database_id}, properties=props)
		print(f"Entry created: {resp['id']}")

def main():
	if not os.getenv('NOTION_API_KEY') or not os.getenv('NOTION_DATABASE_ID'):
		print("Set NOTION_API_KEY and NOTION_DATABASE_ID.")
		return
	JournalEntryAdder().add_entry()

if __name__ == "__main__":
	main()
