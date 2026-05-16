from app.repositories.supabase_client import cleanup_sent_events_db

def run_cleanup():
    cleanup_sent_events_db()
