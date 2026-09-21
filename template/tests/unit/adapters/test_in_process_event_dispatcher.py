from dataclasses import dataclass

from {{ package_name }}.adapters.outbound.events.in_process_event_dispatcher import (
    InProcessEventDispatcher,
)


@dataclass(frozen=True)
class _SomethingHappened:
    thing: str


def test_dispatch_calls_subscribed_handler() -> None:
    dispatcher = InProcessEventDispatcher()
    received: list[_SomethingHappened] = []
    dispatcher.subscribe(_SomethingHappened, received.append)

    dispatcher.dispatch(_SomethingHappened(thing="widget"))

    assert received == [_SomethingHappened(thing="widget")]


def test_dispatch_calls_every_subscriber_for_the_event_type() -> None:
    dispatcher = InProcessEventDispatcher()
    calls: list[str] = []
    dispatcher.subscribe(_SomethingHappened, lambda e: calls.append(f"first:{e.thing}"))
    dispatcher.subscribe(_SomethingHappened, lambda e: calls.append(f"second:{e.thing}"))

    dispatcher.dispatch(_SomethingHappened(thing="widget"))

    assert calls == ["first:widget", "second:widget"]


def test_dispatch_with_no_subscribers_is_a_no_op() -> None:
    dispatcher = InProcessEventDispatcher()

    dispatcher.dispatch(_SomethingHappened(thing="widget"))  # must not raise


def test_dispatch_does_not_call_handlers_for_other_event_types() -> None:
    @dataclass(frozen=True)
    class _OtherEvent:
        pass

    dispatcher = InProcessEventDispatcher()
    received: list[_SomethingHappened] = []
    dispatcher.subscribe(_SomethingHappened, received.append)

    dispatcher.dispatch(_OtherEvent())

    assert received == []
