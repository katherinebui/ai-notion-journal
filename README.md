### AI Notion Journal for Mood/Health Tracking

- **Track**: Date, Mood, Health Status, Activities, Notes in a Notion database.
- **Analyze**: OpenAI for insights + NLTK sentiment.
- **Visualize**: Matplotlib charts for mood/health trends.

### Setup
1) Create a Notion integration, share your database with it, copy Database ID.  
2) Save files above.  
3) `pip install -r requirements.txt`  
4) `cp .env.example .env` and fill `NOTION_API_KEY`, `NOTION_DATABASE_ID`, `OPENAI_API_KEY`.  
   - Optional: set `NOTION_PAGE_ID` and run `setup_notion_database.py` to auto-create the DB.
5) (One-time) `python -c "import nltk; nltk.download('vader_lexicon')"`

### Usage
- Add entry: `python add_journal_entry.py`
- Run analysis: `python ai_journal_tracker.py`
- Quick start: `python quick_start.py`

Outputs:
- `mood_health_trends.png`
- `wellness_report.txt`
