import pytest

from src.output import send_insight


def payload_bytes(text):
    return len(text.encode("utf-8"))


def test_split_short_report_returns_one_chunk():
    chunks = send_insight.split_discord_messages("short report", max_bytes=200)

    assert chunks == ["short report"]


def test_split_long_markdown_prefers_paragraph_boundaries():
    report = "# Title\n\n" + "\n\n".join([f"Paragraph {i} " + ("x" * 40) for i in range(8)])

    chunks = send_insight.split_discord_messages(report, max_bytes=160)

    assert len(chunks) > 1
    assert all(payload_bytes(chunk) <= 160 for chunk in chunks)
    assert "".join(chunks).replace("\n\n", "").replace("\n", "").replace(" ", "").startswith("#TitleParagraph0")


def test_split_hard_splits_single_oversized_block():
    report = "x" * 500

    chunks = send_insight.split_discord_messages(report, max_bytes=120)

    assert len(chunks) > 1
    assert all(payload_bytes(chunk) <= 120 for chunk in chunks)
    assert "".join(chunks) == report


def test_add_chunk_headers_keeps_each_payload_under_limit():
    chunks = ["a" * 80, "b" * 80]

    payloads = send_insight.add_chunk_headers(chunks, title="BTC Monitor AI Report", max_bytes=120)

    assert payloads[0].startswith("**BTC Monitor AI Report (1/2)**")
    assert payloads[1].startswith("**BTC Monitor AI Report (2/2)**")
    assert all(payload_bytes(payload) <= 120 for payload in payloads)


def test_send_content_posts_all_chunks(monkeypatch):
    posted = []

    def fake_post(webhook_url, content, username="BTC Monitor AI"):
        posted.append(content)
        return 204

    monkeypatch.setattr(send_insight, "post_to_discord", fake_post)

    result = send_insight.send_content_to_discord("https://discord.test", "x" * 300, max_bytes=120)

    assert result == 0
    assert len(posted) > 1
    assert posted[0].startswith("**BTC Monitor AI Report (1/")


def test_send_content_stops_on_failed_chunk(monkeypatch):
    posted = []

    def fake_post(webhook_url, content, username="BTC Monitor AI"):
        posted.append(content)
        return 500 if len(posted) == 2 else 204

    monkeypatch.setattr(send_insight, "post_to_discord", fake_post)

    result = send_insight.send_content_to_discord("https://discord.test", "x" * 300, max_bytes=120)

    assert result == 1
    assert len(posted) == 2
