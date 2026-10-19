"""External data feeds — real fetched data injected into observations.

Feeds here are producers only: they populate observation fields the
conditional advisory adapters consume. When a feed is unavailable the
fields simply stay absent and adapters emit their honest no-data status.
"""
