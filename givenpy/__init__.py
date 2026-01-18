import threading
import time
from contextlib import contextmanager

_local = threading.local()


def _log(message, start_time=None):
    if getattr(_local, "trace", False):
        duration = ""
        if start_time:
            duration = f" ({time.time() - start_time:.4f}s)"
        print(f"[trace] {message}{duration}")


@contextmanager
def given(steps=None, trace=False):
    steps = steps or []
    context = type('Context', (), {})()
    started_steps = []

    # Save previous trace state to nested trace works correctly
    prev_trace = getattr(_local, "trace", False)
    _local.trace = trace

    try:
        for step in steps:
            step_name = getattr(step, "__name__", str(step))
            qualname = getattr(step, "__qualname__", "")
            
            if ".<locals>." in qualname:
                # If it's a closure, use the outer function name as the primary name
                factory_name = qualname.split(".<locals>.")[0]
                if step_name == "step":
                    step_name = factory_name
                else:
                    step_name = f"{factory_name}.{step_name}"
            elif hasattr(step, "func"): # handle partials
                step_name = getattr(step.func, "__name__", step_name)
            
            _log(f"Step: {step_name} starting")
            start_time = time.time()
            result = step(context)
            started_steps += [result]
            if result and hasattr(result, "__enter__"):
                result.__enter__()
            _log(f"Step: {step_name} finished", start_time)

        yield context
    except Exception as e:
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
        _local.trace = prev_trace


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
