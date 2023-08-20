from contextlib import contextmanager


@contextmanager
def given(steps=None):
    steps = steps or []
    context = type('Context', (), {})()
    started_steps = []

    try:
        for step in steps:
            result = step(context)
            started_steps += [result]
            if result and hasattr(result, "__enter__"):
                result.__enter__()
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


class Mock:
    """
    Mock class that supports nesting.
    """
    def __getattribute__(self, item):
        return Mock()


@contextmanager
def when(description=None):
    yield Mock()


@contextmanager
def then(message=None):
    yield Mock()


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
