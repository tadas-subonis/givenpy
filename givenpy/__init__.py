import inspect
import time
from contextlib import AsyncExitStack, asynccontextmanager, contextmanager
from contextvars import ContextVar

_trace = ContextVar('givenpy_trace', default=False)


def _log(message, start_time=None):
    if _trace.get():
        duration = ""
        if start_time:
            duration = f" ({time.time() - start_time:.4f}s)"
        print(f"[trace] {message}{duration}")


def _step_name(step):
    step_name = getattr(step, "__name__", str(step))
    qualname = getattr(step, "__qualname__", "")

    if ".<locals>." in qualname:
        factory_name = qualname.split(".<locals>.")[0]
        if step_name == "step":
            step_name = factory_name
        else:
            step_name = f"{factory_name}.{step_name}"
    elif hasattr(step, "func"):
        step_name = getattr(step.func, "__name__", step_name)

    return step_name


@contextmanager
def given(steps=None, trace=False):
    steps = steps or []
    context = type('Context', (), {})()
    started_steps = []
    trace_token = _trace.set(trace)

    try:
        for step in steps:
            step_name = _step_name(step)
            _log(f"Step: {step_name} starting")
            start_time = time.time()
            result = step(context)
            started_steps += [result]
            if result and hasattr(result, "__enter__"):
                result.__enter__()
            _log(f"Step: {step_name} finished", start_time)

        yield context
    except BaseException as e:
        for step in reversed(started_steps):
            result = step
            if result and hasattr(result, "__exit__"):
                result.__exit__(type(e), e, e.__traceback__)
        raise
    else:
        for step in reversed(started_steps):
            result = step
            if result and hasattr(result, "__exit__"):
                result.__exit__(None, None, None)
    finally:
        _trace.reset(trace_token)


@asynccontextmanager
async def agiven(steps=None, trace=False):
    """Run sync or async setup steps and close their resources in reverse order."""
    context = type('Context', (), {})()
    trace_token = _trace.set(trace)

    try:
        async with AsyncExitStack() as resources:
            for step in steps or []:
                step_name = _step_name(step)
                _log(f"Step: {step_name} starting")
                start_time = time.time()
                result = step(context)
                if inspect.isawaitable(result):
                    result = await result
                if result and hasattr(result, "__aenter__"):
                    await resources.enter_async_context(result)
                elif result and hasattr(result, "__enter__"):
                    resources.enter_context(result)
                _log(f"Step: {step_name} finished", start_time)

            yield context
    finally:
        _trace.reset(trace_token)


class Mock:
    """
    Mock class that supports nesting.
    """
    def __getattribute__(self, item):
        return Mock()


@contextmanager
def when(description=None):
    _log(f"When: {description} starting")
    start_time = time.time()
    try:
        yield Mock()
    finally:
        _log(f"When: {description} finished", start_time)


@contextmanager
def then(message=None):
    _log(f"Then: {message} starting")
    start_time = time.time()
    try:
        yield Mock()
    finally:
        _log(f"Then: {message} finished", start_time)


@contextmanager
def resulting(param=None):
    yield Mock()


@contextmanager
def lambda_with(enter, leave):
    enter()
    try:
        yield
    finally:
        leave()


@asynccontextmanager
async def async_lambda_with(enter, leave):
    await enter()
    try:
        yield
    finally:
        await leave()


def loop_steps_iter(iterator, actions):
    def step(context):
        def start():
            for i in iterator:
                for action in actions:
                    result = action(context, i)
                    if result and hasattr(result, "__enter__"):
                        result.__enter__()

        def stop():
            pass

        return lambda_with(start, stop)

    return step
