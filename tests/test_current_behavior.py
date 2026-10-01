"""
How notify-router behaved before any change. These tests were written and
run against the unchanged code; every later change has to keep them green.
"""

from conftest import make_channel, make_rule


def test_first_boot_seeds_the_demo_channels_and_rules(client):
    assert ("httpbin-webhook", "webhook") in client.seeded["channels"]
    assert ("slack-demo", "slack") in client.seeded["channels"]
    assert len(client.seeded["rules"]) == 2


def test_an_event_goes_to_every_matching_rule_highest_priority_first(clean, outbound):
    low = make_channel(clean, "low", "webhook", {"url": "https://low.example/hook"})
    high = make_channel(clean, "high", "webhook", {"url": "https://high.example/hook"})
    make_rule(clean, low, name="all alerts", event_type_filter="alert", priority=1)
    make_rule(clean, high, name="critical", event_type_filter="alert",
              condition_key="severity", condition_value="critical", priority=10)

    response = clean.post("/events", json={"source": "shop", "event_type": "alert", "payload": {"severity": "critical"}})

    assert response.status_code == 202
    body = response.json()
    assert body["matched_rules"] == 2
    assert [d["channel_id"] for d in body["dispatches"]] == [high, low]
    assert [str(r.url) for r in outbound.requests] == ["https://high.example/hook", "https://low.example/hook"]
    assert outbound.bodies()[0] == {
        "source": "shop", "event_type": "alert", "event_id": body["event_id"], "payload": {"severity": "critical"},
    }


def test_conditions_sources_types_and_disabled_rules_filter_events(clean, outbound):
    channel = make_channel(clean, "hook", "webhook", {"url": "https://x.example/hook"})
    make_rule(clean, channel, name="other source", source_filter="bank")
    make_rule(clean, channel, name="other type", event_type_filter="sale")
    make_rule(clean, channel, name="other value", condition_key="severity", condition_value="critical")
    make_rule(clean, channel, name="disabled", enabled=False)

    response = clean.post("/events", json={"source": "shop", "event_type": "alert", "payload": {"severity": "low"}})

    assert response.json()["matched_rules"] == 0
    assert outbound.requests == []


def test_a_failing_channel_still_answers_202_and_is_logged_as_failed(clean, outbound):
    outbound.status = 500
    channel = make_channel(clean, "hook", "webhook", {"url": "https://down.example/hook"})
    make_rule(clean, channel)

    response = clean.post("/events", json={"source": "shop", "event_type": "alert", "payload": {}})

    assert response.status_code == 202
    assert response.json()["dispatches"][0]["status"] == "failed"
    logs = clean.get("/logs", params={"event_id": response.json()["event_id"]}).json()
    assert [log["status"] for log in logs] == ["failed"]


def test_telegram_messages_list_each_payload_field(clean, outbound):
    channel = make_channel(clean, "tg", "telegram", {"bot_token": "TOKEN", "chat_id": "42"})
    make_rule(clean, channel)

    clean.post("/events", json={"source": "shop", "event_type": "alert", "payload": {"item": "Bife", "qty": 3}})

    sent = outbound.bodies()[0]
    assert str(outbound.requests[0].url) == "https://api.telegram.org/botTOKEN/sendMessage"
    assert sent == {
        "chat_id": "42",
        "text": "*[shop]* `alert`\n• *item*: Bife\n• *qty*: 3",
        "parse_mode": "Markdown",
    }


def test_payloads_over_4000_characters_are_rejected(clean):
    response = clean.post("/events", json={"source": "shop", "event_type": "alert", "payload": {"x": "a" * 4100}})

    assert response.status_code == 422


def test_events_are_listed_newest_first(clean, outbound):
    for name in ("first", "second"):
        clean.post("/events", json={"source": name, "event_type": "alert", "payload": {}})

    sources = [e["source"] for e in clean.get("/events").json()]

    assert sources[:2] == ["second", "first"]


def test_events_need_no_credentials_by_default(clean, outbound):
    response = clean.post("/events", json={"source": "shop", "event_type": "alert", "payload": {}})

    assert response.status_code == 202
