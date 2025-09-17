import os
from notion_client import Client
from dotenv import load_dotenv

load_dotenv()

def create_journal_database():
	notion = Client(auth=os.getenv('NOTION_API_KEY'))
	parent_page_id = os.getenv('NOTION_PAGE_ID')
	if not parent_page_id:
		raise RuntimeError("Set NOTION_PAGE_ID in your .env to auto-create the DB.")
	properties = {
		"Date": { "date": {} },
		"Mood": { "select": { "options": [
			{"name": "Happy", "color": "green"},
			{"name": "Excited", "color": "yellow"},
			{"name": "Grateful", "color": "green"},
			{"name": "Content", "color": "blue"},
			{"name": "Neutral", "color": "gray"},
			{"name": "Calm", "color": "blue"},
			{"name": "Tired", "color": "orange"},
			{"name": "Anxious", "color": "red"},
			{"name": "Sad", "color": "red"},
			{"name": "Stressed", "color": "red"},
			{"name": "Frustrated", "color": "red"},
			{"name": "Overwhelmed", "color": "red"}
		]}},
		"Health Status": { "select": { "options": [
			{"name": "Excellent", "color": "green"},
			{"name": "Good", "color": "blue"},
			{"name": "Fair", "color": "yellow"},
			{"name": "Poor", "color": "orange"},
			{"name": "Sick", "color": "red"}
		]}},
		"Activities": { "rich_text": {} },
		"Notes": { "rich_text": {} }
	}
	resp = notion.databases.create(
		parent={ "type": "page_id", "page_id": parent_page_id },
		title=[{ "type": "text", "text": { "content": "AI Wellness Journal" } }],
		properties=properties
	)
	print("Database created.")
	print(f"NOTION_DATABASE_ID={resp['id']}")
	return resp['id']

def add_sample_entries():
	notion = Client(auth=os.getenv('NOTION_API_KEY'))
	db_id = os.getenv('NOTION_DATABASE_ID')
	if not db_id:
		print("Set NOTION_DATABASE_ID to add samples.")
		return
	samples = [
		{
			"Date": {"date": {"start": "2025-09-10"}},
			"Mood": {"select": {"name": "Happy"}},
			"Health Status": {"select": {"name": "Good"}},
			"Activities": {"rich_text": [{"text": {"content": "Workout, deep work, dinner with friends"}}]},
			"Notes": {"rich_text": [{"text": {"content": "Felt focused and social."}}]}
		},
		{
			"Date": {"date": {"start": "2025-09-11"}},
			"Mood": {"select": {"name": "Tired"}},
			"Health Status": {"select": {"name": "Fair"}},
			"Activities": {"rich_text": [{"text": {"content": "Meetings, errands, reading"}}]},
			"Notes": {"rich_text": [{"text": {"content": "Low energy after meetings."}}]}
		}
	]
	for p in samples:
		notion.pages.create(parent={"database_id": db_id}, properties=p)
	print(f"Added {len(samples)} sample entries.")

if __name__ == "__main__":
	if not os.getenv('NOTION_API_KEY'):
		print("Set NOTION_API_KEY.")
		exit(1)
	# create_journal_database()
	# add_sample_entries()
	print("To auto-create the DB: set NOTION_PAGE_ID and uncomment create_journal_database().")
