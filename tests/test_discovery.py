"""Tests for URL canonicalization and content hashing (pure logic)."""

from fulcrumnews.services.discovery.base import canonicalize_url, content_hash


def test_canonicalize_forces_https_and_strips_fragment():
    assert canonicalize_url("http://example.com/a/b#frag") == "https://example.com/a/b"


def test_canonicalize_strips_tracking_params():
    url = "https://news.com/story?utm_source=tw&id=5&fbclid=xyz&gclid=1"
    assert canonicalize_url(url) == "https://news.com/story?id=5"


def test_canonicalize_strips_trailing_slash():
    assert canonicalize_url("https://example.com/path/") == "https://example.com/path"


def test_canonicalize_lowercases_host():
    assert canonicalize_url("https://Example.COM/Path") == "https://example.com/Path"


def test_canonicalize_is_idempotent():
    once = canonicalize_url("http://Example.com/x/?utm_medium=a#y")
    assert canonicalize_url(once) == once


def test_content_hash_ignores_whitespace_and_case():
    assert content_hash("Hello   World") == content_hash("hello world")


def test_content_hash_distinguishes_content():
    assert content_hash("a story") != content_hash("another story")


def test_content_hash_empty_is_none():
    assert content_hash("") is None
    assert content_hash(None) is None
    assert content_hash("   ") is None
