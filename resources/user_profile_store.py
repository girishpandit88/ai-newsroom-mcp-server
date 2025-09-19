def get_user_profile(user_id: str):
    """Return mock user profile."""
    return {
        "user_id": user_id,
        "preferred_topics": ["AI", "Tech"],
        "blocked_sources": ["fake-news.com"]
    }
