import asyncio

from jarvis.core.approvals import ApprovalManager, Risk
from jarvis.core.events import EventBus


async def test_below_threshold_auto_approved():
    approvals = ApprovalManager(EventBus(), threshold=2)
    assert await approvals.request("skill:read", "x", Risk.READ) is True
    assert await approvals.request("skill:write", "x", Risk.WRITE) is True


async def test_requires_user_decision():
    bus = EventBus()
    approvals = ApprovalManager(bus, threshold=1, timeout=2)
    seen = {}

    async def on_request(event):
        seen.update(event.data)
        await approvals.resolve(event.data["id"], approved=True)

    bus.subscribe("approval.requested", on_request)
    ok = await approvals.request("skill:write_file", "path=/tmp/x", Risk.WRITE)
    assert ok is True
    assert seen["action"] == "skill:write_file"


async def test_denied():
    bus = EventBus()
    approvals = ApprovalManager(bus, threshold=1, timeout=2)

    async def on_request(event):
        await approvals.resolve(event.data["id"], approved=False)

    bus.subscribe("approval.requested", on_request)
    assert await approvals.request("skill:delete", "x", Risk.CRITICAL) is False


async def test_timeout_denies():
    approvals = ApprovalManager(EventBus(), threshold=0, timeout=0.05)
    assert await approvals.request("skill:x", "d", Risk.READ) is False


async def test_session_grant():
    bus = EventBus()
    approvals = ApprovalManager(bus, threshold=1, timeout=2)
    decisions = []

    async def on_request(event):
        decisions.append(event.data["id"])
        await approvals.resolve(event.data["id"], approved=True, remember=True)

    bus.subscribe("approval.requested", on_request)
    await approvals.request("skill:write_file", "1", Risk.WRITE)
    await approvals.request("skill:write_file", "2", Risk.WRITE)
    # Second call passed silently thanks to the session grant.
    assert len(decisions) == 1


async def test_concurrent_requests():
    bus = EventBus()
    approvals = ApprovalManager(bus, threshold=1, timeout=2)

    async def on_request(event):
        await asyncio.sleep(0.01)
        await approvals.resolve(event.data["id"], approved=True)

    bus.subscribe("approval.requested", on_request)
    results = await asyncio.gather(
        approvals.request("a", "1", Risk.WRITE),
        approvals.request("b", "2", Risk.WRITE),
    )
    assert results == [True, True]
