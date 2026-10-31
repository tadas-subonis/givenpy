---
name: givenpy-behavior-tests
description: Write, improve, or review Python behavior tests in projects using GivenPy and PyHamcrest. Use for readable given/when/then scenarios, reusable setup and cleanup, and synchronous or asynchronous application behavior.
---

# GivenPy behavior tests

Use this skill in the application being tested. Follow its testing policy, dependency
management, test runner, and isolation rules. GivenPy structures scenarios; the project's
runner still collects and executes tests.

## Choose a meaningful scenario

- State the caller-visible behavior and what a failure would catch. Exercise the smallest
  useful boundary: a public function for pure logic, or the real API, database, or worker
  path when that interaction is the behavior being tested.
- Name the test after the outcome. Use explicit setup, one action in `when`, and observable
  expectations in `then`. Multiple assertions may describe the same outcome.
- Use the real implementation for the behavior under test. Stub unrelated external services
  only at a clear boundary. Mocked calls, source wording, or successful execution alone do
  not prove the application's behavior.
- Derive expected values from the requirement, not by repeating the implementation. Include
  a failure or boundary case when it protects a concrete regression.

## Set up and clean up

Prefer small parameterized step factories returning a `step(context)` function. Store only
scenario data and resources on the context. Reuse existing project fixtures for shared
infrastructure; keep the scenario's required state visible in its steps. Clean up only
resources owned by the test and preserve isolation between tests.

For synchronous resources, a step may return a context manager, including
`lambda_with(enter, leave)`. Set context attributes during setup; GivenPy does not assign
the context manager's yielded value to an attribute for you. Release resources even when
an assertion fails.

This example assumes the application's `Account` API; adapt the import and setup to the
actual project rather than implementing application behavior inside the test:

```python
from app.accounts import Account
from givenpy import given, when, then
from hamcrest import assert_that, equal_to


def an_account_with_balance(amount):
    def step(context):
        context.account = Account(balance=amount)
    return step


def test_withdrawal_reduces_available_balance():
    with given([an_account_with_balance(10)]) as context:
        with when("the owner withdraws 3"):
            context.account.withdraw(3)
        with then("7 remains available"):
            assert_that(context.account.balance, equal_to(7))
```

## Asynchronous scenarios

Check the actual test environment's installed GivenPy API before importing `agiven` or
`async_lambda_with`; older releases do not provide them. A checkout's documentation does
not establish what the consumer's pinned dependency supports. Add or upgrade dependencies
through the project's normal workflow when within scope; otherwise report the blocker.

- With synchronous setup, ordinary `with given(...)` works inside an async test. Await the
  action inside ordinary `with when(...)`; `when` and `then` are synchronous blocks.
- When setup must await work or own async resources, use `async with agiven(...)` if
  available. It accepts sync and async steps and resource context managers, and unwinds
  entered resources in reverse order.
- Return `async_lambda_with(enter, leave)` for paired async setup and cleanup. Both callbacks
  must be awaitable. If setup fails after partially allocating a resource, that setup must
  release it; teardown cannot clean up a resource that never finished entering.
- Use the project's async runner and event-loop fixtures. Do not nest `asyncio.run` inside
  a running event loop or pass an async setup step to synchronous `given`.

For example, assuming the application's async session API and an async-capable runner:

```python
from app.accounts import open_account_session
from givenpy import agiven, async_lambda_with, when, then
from hamcrest import assert_that, equal_to


def an_account_session_with_balance(amount):
    def step(context):
        async def enter():
            context.session = await open_account_session(balance=amount)

        async def leave():
            await context.session.close()

        return async_lambda_with(enter, leave)
    return step


async def test_async_withdrawal_reduces_available_balance():
    async with agiven([an_account_session_with_balance(10)]) as context:
        with when("the owner withdraws 3"):
            await context.session.withdraw(3)
        with then("7 remains available"):
            assert_that(await context.session.balance(), equal_to(7))
```

Apply the project's required async test marker or configuration to that example.

## Assert and verify

Use `hamcrest.assert_that(actual, matcher)` for values, persisted state, responses, or
emitted effects that matter to the scenario. Prefer direct matchers over asserting a
boolean expression: `assert_that(items, has_item(expected))` gives a more useful failure
than `assert_that(expected in items, equal_to(True))`. Extract complex nested matchers
into behavior-named helpers when that improves readability.

Run the focused test through the project's canonical command, then the relevant required
suite. For a regression, demonstrate that it fails with the broken behavior and passes
with the fix when an isolated baseline is practical. Report the command, result, and
coverage limits; do not equate a passing test with untested end-to-end functionality.
