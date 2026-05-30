"""Default outlet roster — first-run seed data only.

Outlets are fully runtime-editable via the admin UI; this list just bootstraps a
balanced (~2 left / 2 center / 2 right) set of free outlets on first launch.
Reuters & AFP are intentionally excluded (no free/legal feed). Lean ratings are a
consensus of AllSides / Media Bias Fact Check / Ad Fontes Media.
"""

from __future__ import annotations

from .models.enums import FeedType, Lean


def _rss(name: str, slug: str, lean: Lean, feed_url: str, homepage: str, enabled: bool = True) -> dict:
    """Shorthand for an RSS outlet roster entry."""
    return {
        "name": name,
        "slug": slug,
        "lean": lean,
        "feed_type": FeedType.RSS,
        "feed_url": feed_url,
        "homepage": homepage,
        "enabled": enabled,
    }


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
    # ── More UK outlets ──────────────────────────────────────────────────────
    _rss("i (inews)", "inews", Lean.CENTER, "https://inews.co.uk/feed", "https://inews.co.uk"),
    _rss("Channel 4 News", "channel4", Lean.CENTER, "https://www.channel4.com/news/feed", "https://www.channel4.com/news"),
    _rss("New Statesman", "newstatesman", Lean.LEFT, "https://www.newstatesman.com/feed", "https://www.newstatesman.com"),
    _rss("The Canary", "thecanary", Lean.LEFT, "https://www.thecanary.co/feed/", "https://www.thecanary.co"),
    _rss("UnHerd", "unherd", Lean.LEAN_RIGHT, "https://unherd.com/feed/", "https://unherd.com"),
    _rss("Daily Star", "dailystar", Lean.RIGHT, "https://www.dailystar.co.uk/?service=rss", "https://www.dailystar.co.uk"),
    # ── US outlets ───────────────────────────────────────────────────────────
    _rss("Vox", "vox", Lean.LEFT, "https://www.vox.com/rss/index.xml", "https://www.vox.com"),
    _rss("Mother Jones", "motherjones", Lean.LEFT, "https://www.motherjones.com/feed/", "https://www.motherjones.com"),
    _rss("The Intercept", "theintercept", Lean.LEFT, "https://theintercept.com/feed/?rss", "https://theintercept.com"),
    _rss("Slate", "slate", Lean.LEFT, "https://slate.com/feeds/all.rss", "https://slate.com"),
    _rss("CNN", "cnn", Lean.LEAN_LEFT, "http://rss.cnn.com/rss/cnn_topstories.rss", "https://www.cnn.com"),
    _rss("NBC News", "nbcnews", Lean.LEAN_LEFT, "https://feeds.nbcnews.com/nbcnews/public/news", "https://www.nbcnews.com"),
    _rss("ABC News", "abcnews", Lean.LEAN_LEFT, "https://abcnews.go.com/abcnews/topstories", "https://abcnews.go.com"),
    _rss("Politico", "politico", Lean.LEAN_LEFT, "https://rss.politico.com/politics-news.xml", "https://www.politico.com"),
    _rss("The New York Times", "nytimes", Lean.LEAN_LEFT, "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml", "https://www.nytimes.com"),
    _rss("NPR", "npr", Lean.CENTER, "https://feeds.npr.org/1001/rss.xml", "https://www.npr.org"),
    _rss("CBS News", "cbsnews", Lean.CENTER, "https://www.cbsnews.com/latest/rss/main", "https://www.cbsnews.com"),
    _rss("Newsweek", "newsweek", Lean.CENTER, "https://www.newsweek.com/rss", "https://www.newsweek.com"),
    _rss("The Hill", "thehill", Lean.CENTER, "https://thehill.com/news/feed/", "https://thehill.com"),
    _rss("Fox News", "foxnews", Lean.RIGHT, "https://moxie.foxnews.com/google-publisher/latest.xml", "https://www.foxnews.com"),
    _rss("New York Post", "nypost", Lean.RIGHT, "https://nypost.com/feed/", "https://nypost.com"),
    _rss("Washington Examiner", "waexaminer", Lean.RIGHT, "https://www.washingtonexaminer.com/feed/", "https://www.washingtonexaminer.com"),
    _rss("National Review", "nationalreview", Lean.RIGHT, "https://www.nationalreview.com/feed/", "https://www.nationalreview.com"),
    _rss("The Federalist", "federalist", Lean.RIGHT, "https://thefederalist.com/feed/", "https://thefederalist.com"),
    _rss("The Washington Times", "washtimes", Lean.RIGHT, "https://www.washingtontimes.com/rss/headlines/news/politics/", "https://www.washingtontimes.com"),
    _rss("The Daily Wire", "dailywire", Lean.RIGHT, "https://www.dailywire.com/feeds/rss.xml", "https://www.dailywire.com"),
    _rss("Breitbart", "breitbart", Lean.RIGHT, "https://feeds.feedburner.com/breitbart", "https://www.breitbart.com"),
    # ── International ─────────────────────────────────────────────────────────
    _rss("DW (Deutsche Welle)", "dw", Lean.CENTER, "https://rss.dw.com/rdf/rss-en-all", "https://www.dw.com"),
    _rss("France 24", "france24", Lean.CENTER, "https://www.france24.com/en/rss", "https://www.france24.com/en/"),
    _rss("ABC News (Australia)", "abcau", Lean.CENTER, "https://www.abc.net.au/news/feed/51120/rss.xml", "https://www.abc.net.au/news"),
    # ── More US ──────────────────────────────────────────────────────────────
    _rss("The Atlantic", "theatlantic", Lean.LEFT, "https://www.theatlantic.com/feed/all/", "https://www.theatlantic.com"),
    _rss("The New Yorker", "newyorker", Lean.LEFT, "https://www.newyorker.com/feed/everything", "https://www.newyorker.com"),
    _rss("Salon", "salon", Lean.LEFT, "https://www.salon.com/feed/", "https://www.salon.com"),
    _rss("Jacobin", "jacobin", Lean.LEFT, "https://jacobin.com/feed/", "https://jacobin.com"),
    _rss("The Daily Beast", "dailybeast", Lean.LEFT, "https://www.thedailybeast.com/arc/outboundfeeds/rss/", "https://www.thedailybeast.com"),
    _rss("Common Dreams", "commondreams", Lean.LEFT, "https://www.commondreams.org/feeds/news.rss", "https://www.commondreams.org"),
    _rss("ProPublica", "propublica", Lean.LEAN_LEFT, "https://www.propublica.org/feeds/propublica/main", "https://www.propublica.org"),
    _rss("Axios", "axios", Lean.CENTER, "https://api.axios.com/feed/", "https://www.axios.com"),
    _rss("CNBC", "cnbc", Lean.CENTER, "https://www.cnbc.com/id/100003114/device/rss/rss.html", "https://www.cnbc.com"),
    _rss("Business Insider", "businessinsider", Lean.CENTER, "https://www.businessinsider.com/rss", "https://www.businessinsider.com"),
    _rss("Reason", "reason", Lean.LEAN_RIGHT, "https://reason.com/latest/feed/", "https://reason.com"),
    _rss("Washington Free Beacon", "freebeacon", Lean.RIGHT, "https://freebeacon.com/feed/", "https://freebeacon.com"),
    # ── More UK ──────────────────────────────────────────────────────────────
    _rss("Left Foot Forward", "leftfootforward", Lean.LEFT, "https://leftfootforward.org/feed/", "https://leftfootforward.org"),
    _rss("PinkNews", "pinknews", Lean.LEFT, "https://www.thepinknews.com/feed/", "https://www.thepinknews.com"),
    _rss("spiked", "spiked", Lean.LEAN_RIGHT, "https://www.spiked-online.com/feed/", "https://www.spiked-online.com"),
    _rss("The Critic", "thecritic", Lean.LEAN_RIGHT, "https://thecritic.co.uk/feed/", "https://thecritic.co.uk"),
    _rss("ConservativeHome", "conservativehome", Lean.RIGHT, "https://conservativehome.com/feed", "https://conservativehome.com"),
]
