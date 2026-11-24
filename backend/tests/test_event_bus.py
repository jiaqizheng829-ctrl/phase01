import logging
from dataclasses import dataclass

from app.domain.events.bus import EventBus


@dataclass(frozen=True)
class ExampleEvent:
    value: int


@dataclass(frozen=True)
class OtherEvent:
    value: int


def test_handlers_run_in_subscription_order():
    bus = EventBus()
    calls = []
    event = ExampleEvent(10)

    bus.subscribe(
        ExampleEvent,
        lambda received: calls.append(("first", received)),
    )
    bus.subscribe(
        ExampleEvent,
        lambda received: calls.append(("second", received)),
    )

    bus.publish(event)

    assert calls == [
        ("first", event),
        ("second", event),
    ]


def test_only_matching_event_type_is_notified():
    bus = EventBus()
    received = []

    bus.subscribe(ExampleEvent, received.append)
    bus.publish(OtherEvent(10))

    assert received == []


def test_publish_without_subscribers_is_allowed():
    bus = EventBus()
    bus.publish(ExampleEvent(10))


def test_failed_subscriber_is_logged_and_later_handler_runs(caplog):
    bus = EventBus()
    calls = []

    def broken(event):
        calls.append("broken")
        raise RuntimeError("Subscriber test failure")

    def healthy(event):
        calls.append("healthy")

    bus.subscribe(ExampleEvent, broken)
    bus.subscribe(ExampleEvent, healthy)

    with caplog.at_level(
        logging.ERROR,
        logger="app.domain.events.bus",
    ):
        bus.publish(ExampleEvent(10))

    assert calls == ["broken", "healthy"]
    assert "Subscriber test failure" in caplog.text
    assert "ExampleEvent" in caplog.text


def test_subscription_added_during_publish_starts_next_time():
    bus = EventBus()
    calls = []
    registered = False

    def later(event):
        calls.append("later")

    def first(event):
        nonlocal registered
        calls.append("first")

        if not registered:
            bus.subscribe(ExampleEvent, later)
            registered = True

    bus.subscribe(ExampleEvent, first)

    bus.publish(ExampleEvent(1))
    assert calls == ["first"]

    calls.clear()
    bus.publish(ExampleEvent(2))
    assert calls == ["first", "later"]


def test_subscriber_can_publish_another_event():
    bus = EventBus()
    calls = []

    def translate(event):
        calls.append("reading")
        bus.publish(OtherEvent(event.value))

    def receive(event):
        calls.append(("threshold", event.value))

    bus.subscribe(ExampleEvent, translate)
    bus.subscribe(OtherEvent, receive)

    bus.publish(ExampleEvent(10))

    assert calls == ["reading", ("threshold", 10)]