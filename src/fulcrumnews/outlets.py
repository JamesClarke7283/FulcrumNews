"""Default outlet roster — first-run seed data only.

Outlets are fully runtime-editable via the admin UI; this list just bootstraps a
balanced (~2 left / 2 center / 2 right) set of free outlets on first launch.
Reuters & AFP are intentionally excluded (no free/legal feed). Lean ratings are a
consensus of AllSides / Media Bias Fact Check / Ad Fontes Media.
"""

from __future__ import annotations

from .models.enums import FeedType, Lean

DEFAULT_OUTLET_ROSTER: list[dict] = [
    {
        "name": "The Guardian",
        "slug": "guardian",
        "lean": Lean.LEFT,
        "feed_type": FeedType.GUARDIAN_API,
        # Guardian uses the Open Platform API; "section" picks the desk.
        "feed_url": "world",
        "homepage": "https://www.theguardian.com",
        "enabled": True,
        "config": {"section": "world"},
    },
    {
        "name": "Daily Mirror",
        "slug": "mirror",
        "lean": Lean.LEAN_LEFT,
        "feed_type": FeedType.RSS,
        "feed_url": "https://www.mirror.co.uk/news/?service=rss",
        "homepage": "https://www.mirror.co.uk",
        "enabled": True,
    },
    {
        "name": "The Independent",
        "slug": "independent",
        "lean": Lean.LEAN_LEFT,
        "feed_type": FeedType.RSS,
        "feed_url": "https://www.independent.co.uk/news/world/rss",
        "homepage": "https://www.independent.co.uk",
        "enabled": False,  # lean-left already covered by Mirror; enable to widen spread
    },
    {
        "name": "Al Jazeera English",
        "slug": "aljazeera",
        "lean": Lean.LEAN_LEFT,
        "feed_type": FeedType.RSS,
        "feed_url": "https://www.aljazeera.com/xml/rss/all.xml",
        "homepage": "https://www.aljazeera.com",
        "enabled": False,
    },
    {
        "name": "BBC News",
        "slug": "bbc",
        "lean": Lean.CENTER,
        "feed_type": FeedType.RSS,
        "feed_url": "https://feeds.bbci.co.uk/news/world/rss.xml",
        "homepage": "https://www.bbc.co.uk/news",
        "enabled": True,
    },
    {
        "name": "Sky News",
        "slug": "skynews",
        "lean": Lean.CENTER,
        "feed_type": FeedType.RSS,
        "feed_url": "https://feeds.skynews.com/feeds/rss/world.xml",
        "homepage": "https://news.sky.com",
        "enabled": True,
    },
    {
        "name": "GB News",
        "slug": "gbnews",
        "lean": Lean.LEAN_RIGHT,
        "feed_type": FeedType.RSS,
        "feed_url": "https://www.gbnews.com/feeds/news.rss",
        "homepage": "https://www.gbnews.com",
        "enabled": True,
    },
    {
        "name": "The Telegraph",
        "slug": "telegraph",
        "lean": Lean.LEAN_RIGHT,
        "feed_type": FeedType.RSS,
        "feed_url": "https://www.telegraph.co.uk/news/rss.xml",
        "homepage": "https://www.telegraph.co.uk",
        # Off by default: article pages are paywalled (HTTP 402), so bodies can't be
        # extracted — only headlines/snippets. Enable if you have access.
        "enabled": False,
    },
    {
        "name": "Daily Mail",
        "slug": "dailymail",
        "lean": Lean.RIGHT,
        "feed_type": FeedType.RSS,
        "feed_url": "https://www.dailymail.co.uk/news/index.rss",
        "homepage": "https://www.dailymail.co.uk",
        "enabled": True,
    },
    # ── Additional free outlets (validated: reachable, parse, full-text extractable) ──
    {
        "name": "openDemocracy",
        "slug": "opendemocracy",
        "lean": Lean.LEFT,
        "feed_type": FeedType.RSS,
        "feed_url": "https://www.opendemocracy.net/en/rss/",
        "homepage": "https://www.opendemocracy.net",
        "enabled": True,
    },
    {
        "name": "Novara Media",
        "slug": "novara",
        "lean": Lean.LEFT,
        "feed_type": FeedType.RSS,
        "feed_url": "https://novaramedia.com/feed/",
        "homepage": "https://novaramedia.com",
        "enabled": True,
    },
    {
        "name": "Morning Star",
        "slug": "morningstar",
        "lean": Lean.LEFT,
        "feed_type": FeedType.RSS,
        "feed_url": "https://morningstaronline.co.uk/rss.xml",
        "homepage": "https://morningstaronline.co.uk",
        "enabled": False,  # defined for breadth; enable to widen the left
    },
    {
        "name": "The National (Scotland)",
        "slug": "nationalscot",
        "lean": Lean.LEAN_LEFT,
        "feed_type": FeedType.RSS,
        "feed_url": "https://www.thenational.scot/news/rss/",
        "homepage": "https://www.thenational.scot",
        "enabled": True,
    },
    {
        "name": "Metro",
        "slug": "metro",
        "lean": Lean.CENTER,
        "feed_type": FeedType.RSS,
        "feed_url": "https://metro.co.uk/news/feed/",
        "homepage": "https://metro.co.uk",
        "enabled": True,
    },
    {
        "name": "Evening Standard",
        "slug": "standard",
        "lean": Lean.CENTER,
        "feed_type": FeedType.RSS,
        "feed_url": "https://www.standard.co.uk/news/rss",
        "homepage": "https://www.standard.co.uk",
        "enabled": True,
    },
    {
        "name": "The Conversation",
        "slug": "conversation",
        "lean": Lean.CENTER,
        "feed_type": FeedType.RSS,
        "feed_url": "https://theconversation.com/uk/articles.atom",
        "homepage": "https://theconversation.com/uk",
        "enabled": True,
    },
    {
        "name": "The Sun",
        "slug": "thesun",
        "lean": Lean.RIGHT,
        "feed_type": FeedType.RSS,
        "feed_url": "https://www.thesun.co.uk/news/feed/",
        "homepage": "https://www.thesun.co.uk",
        "enabled": True,
    },
    {
        "name": "Daily Express",
        "slug": "express",
        "lean": Lean.RIGHT,
        "feed_type": FeedType.RSS,
        "feed_url": "https://www.express.co.uk/posts/rss/1/news",
        "homepage": "https://www.express.co.uk",
        "enabled": True,
    },
]
