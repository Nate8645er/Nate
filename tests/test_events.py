import asyncio

from jarvis.core.events import Event, EventBus


async def test_publish_and_subscribe():
    bus = EventBus()
    received: list[Event] = []

    async def handler(event: Event) -> None:
        received.append(event)

    bus.subscribe("chat.*", handler)
    await bus.publish("chat.user", {"text": "hi"})
    await bus.publish("system.online", {})  # should not match

    assert len(received) == 1
    assert received[0].topic == "chat.user"
    assert received[0].data["text"] == "hi"


async def test_unsubscribe():
    bus = EventBus()
    hits = []

    async def handler(event: Event) -> None:
        hits.append(event)

    unsub = bus.subscribe("*", handler)
    await bus.publish("a", {})
    unsub()
    await bus.publish("b", {})
    assert len(hits) == 1


async def test_wait_for():
    bus = EventBus()

    async def fire() -> None:
        await asyncio.sleep(0.01)
        await bus.publish("done", {"ok": True})

    asyncio.get_running_loop().create_task(fire())
    event = await bus.wait_for("done", timeout=1)
    assert event.data["ok"] is True


async def test_history_bounded():
    bus = EventBus(history_size=3)
    for i in range(5):
        await bus.publish(f"e{i}", {})
    assert [e.topic for e in bus.history] == ["e2", "e3", "e4"]
