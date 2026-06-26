"""Relative navigate-URL resolution (round-3 piece C).

planner-sees-start-url made the LLM emit site-relative navigations (e.g.
"library/json.html"), which page.goto rejects as an invalid URL. The executor now
resolves them against the current page; absolute / data: / about: pass through.
"""

from app.agent.act import _resolve_url


class _Page:
    def __init__(self, url):
        self.url = url


def test_relative_resolves_against_current_page():
    p = _Page("https://docs.python.org/3/")
    assert _resolve_url(p, "library/json.html") == "https://docs.python.org/3/library/json.html"


def test_absolute_and_scheme_urls_pass_through():
    p = _Page("https://docs.python.org/3/")
    assert _resolve_url(p, "https://example.com/x") == "https://example.com/x"
    assert _resolve_url(p, "data:text/html,hi") == "data:text/html,hi"
    assert _resolve_url(p, "#frag") == "#frag"


def test_no_real_base_leaves_relative_unchanged():
    # First navigation (page at about:blank) can't resolve a relative URL; pass it
    # through rather than fabricate a base.
    assert _resolve_url(_Page("about:blank"), "library/x") == "library/x"
