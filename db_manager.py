from database import connect

def get_connection():
    """Ensures compatibility by routing legacy calls to the main database helper."""
    return connect()