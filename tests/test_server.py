import pytest
import requests

import server


README = """\
# Shared Solutions

- [wc](Solutions/challenge-wc/solution.md)
- [wc in Go](Solutions/challenge-wc/go-solution.md)
- [redis](Solutions/challenge-redis/python-solution.md)
- a mention of challenge-json-parser with no link
- [not markdown](Solutions/challenge-wc/notes.txt)
"""


@pytest.fixture(autouse=True)
def stub_network(monkeypatch):
    """Serve a canned README instead of hitting GitHub."""
    monkeypatch.setattr(server, "_fetch", lambda url: README)


def test_solution_finder_returns_every_matching_path():
    assert server.CodingChallengesSolutionFinder("wc") == [
        "Solutions/challenge-wc/solution.md",
        "Solutions/challenge-wc/go-solution.md",
    ]


def test_solution_finder_is_case_insensitive():
    assert server.CodingChallengesSolutionFinder("REDIS") == [
        "Solutions/challenge-redis/python-solution.md"
    ]


def test_solution_finder_ignores_non_markdown_links():
    assert "Solutions/challenge-wc/notes.txt" not in server.CodingChallengesSolutionFinder("wc")


def test_solution_finder_returns_empty_list_for_unknown_challenge():
    assert server.CodingChallengesSolutionFinder("nonexistent") == []


@pytest.mark.parametrize("name", ["", "   "])
def test_solution_finder_rejects_blank_name(name):
    with pytest.raises(ValueError):
        server.CodingChallengesSolutionFinder(name)


def test_list_all_challenges_is_sorted_and_deduplicated():
    assert server.ListAllChallenges() == ["json-parser", "redis", "wc"]


def test_read_solution_fetches_url_under_repo_root(monkeypatch):
    requested = []
    monkeypatch.setattr(server, "_fetch", lambda url: requested.append(url) or "file body")

    assert server.ReadSolution("Solutions/challenge-wc/solution.md") == "file body"
    assert requested == [server.URL + "Solutions/challenge-wc/solution.md"]


def test_read_solution_strips_leading_slash(monkeypatch):
    requested = []
    monkeypatch.setattr(server, "_fetch", lambda url: requested.append(url) or "body")

    server.ReadSolution("/Solutions/challenge-wc/solution.md")

    assert requested == [server.URL + "Solutions/challenge-wc/solution.md"]


@pytest.mark.parametrize("path", ["", "   "])
def test_read_solution_rejects_blank_path(path):
    with pytest.raises(ValueError):
        server.ReadSolution(path)


def test_fetch_wraps_network_errors(monkeypatch):
    def boom(url, timeout):
        raise requests.exceptions.Timeout("too slow")

    monkeypatch.setattr(server.requests, "get", boom)

    with pytest.raises(Exception, match="Failed to fetch"):
        server._fetch("https://example.com/README.md")
