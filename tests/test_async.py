import asyncio

import pytest
from hamcrest import assert_that, equal_to

from givenpy import agiven, async_lambda_with, given, lambda_with, then, when


def a_connected_service(events):
    async def step(context):
        async def connect():
            events.append("connect")
            context.connected = True

        async def disconnect():
            events.append("disconnect")
            context.connected = False

        return async_lambda_with(connect, disconnect)

    return step


def test_async_step_can_prepare_and_clean_up_a_service():
    events = []

    async def scenario():
        async with agiven([a_connected_service(events)]) as context:
            with when("the connected service handles a request"):
                await asyncio.sleep(0)
                result = "ready" if context.connected else "unavailable"

            with then("it returns a ready result"):
                assert_that(result, equal_to("ready"))

        assert_that(context.connected, equal_to(False))

    asyncio.run(scenario())
    assert_that(events, equal_to(["connect", "disconnect"]))


def test_agiven_closes_mixed_resources_in_reverse_order_after_setup_failure():
    events = []

    def sync_resource(context):
        return lambda_with(lambda: events.append("sync open"),
                           lambda: events.append("sync close"))

    async def failed_setup(context):
        events.append("failed setup")
        raise RuntimeError("setup failed")

    async def scenario():
        with pytest.raises(RuntimeError, match="setup failed"):
            async with agiven([sync_resource, a_connected_service(events), failed_setup]):
                pass

    asyncio.run(scenario())
    assert_that(events, equal_to([
        "sync open", "connect", "failed setup", "disconnect", "sync close"
    ]))


def test_agiven_closes_resources_when_the_test_body_fails():
    events = []

    async def scenario():
        with pytest.raises(ValueError, match="request failed"):
            async with agiven([a_connected_service(events)]):
                with when("the request fails"):
                    raise ValueError("request failed")

    asyncio.run(scenario())
    assert_that(events, equal_to(["connect", "disconnect"]))


def test_agiven_closes_resources_when_the_test_is_cancelled():
    events = []

    async def scenario():
        with pytest.raises(asyncio.CancelledError):
            async with agiven([a_connected_service(events)]):
                raise asyncio.CancelledError()

    asyncio.run(scenario())
    assert_that(events, equal_to(["connect", "disconnect"]))


def test_async_trace_does_not_leak_to_another_task(capsys):
    async def scenario():
        traced_started = asyncio.Event()
        plain_finished = asyncio.Event()

        async def traced():
            async with agiven(trace=True):
                traced_started.set()
                await plain_finished.wait()
                with when("traced request"):
                    pass

        async def plain():
            await traced_started.wait()
            async with agiven(trace=False):
                with when("plain request"):
                    pass
            plain_finished.set()

        await asyncio.gather(traced(), plain())

    asyncio.run(scenario())
    output = capsys.readouterr().out
    assert_that("[trace] When: traced request starting" in output, equal_to(True))
    assert_that("plain request" in output, equal_to(False))


def test_sync_given_still_works_inside_an_async_test():
    async def scenario():
        with given([lambda context: setattr(context, "number", 2)]) as context:
            with when("an async operation adds five"):
                await asyncio.sleep(0)
                result = context.number + 5

            with then("the result is seven"):
                assert_that(result, equal_to(7))

    asyncio.run(scenario())


def test_sync_given_closes_resources_when_an_async_test_is_cancelled():
    events = []

    def sync_resource(context):
        return lambda_with(lambda: events.append("open"),
                           lambda: events.append("close"))

    async def scenario():
        with pytest.raises(asyncio.CancelledError):
            with given([sync_resource]):
                raise asyncio.CancelledError()

    asyncio.run(scenario())
    assert_that(events, equal_to(["open", "close"]))
