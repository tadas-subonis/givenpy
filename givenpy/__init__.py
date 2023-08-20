class GivenScope:
    def __init__(self, steps):
        self.steps = steps or []

        class Context:
            pass

        self.context = Context()
        self.started_steps = []

    def __enter__(self):
        context = self.context
        if self.steps:
            for step in self.steps:
                result = step(context)
                self.started_steps += [result]
                if result and hasattr(result, "__enter__"):
                    result.__enter__()
        return context

    def __exit__(self, type, value, traceback):
        for step in reversed(self.started_steps):
            result = step
            if result and hasattr(result, "__exit__"):
                result.__exit__(type, value, traceback)


def given(steps=None):
    return GivenScope(steps)


def when(description=None):
    return MockWith()


def then(message=None):
    return MockWith()


class MockWith:
    def __enter__(self):
        pass

    def __exit__(self, type, value, traceback):
        pass

    def __getattribute__(self, item):
        return MockWith()


class LambdaWith:
    def __init__(self, enter, leave):
        self.enter = enter
        self.leave = leave

    def __enter__(self):
        self.enter()

    def __exit__(self, type, value, traceback):
        self.leave()


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

        return LambdaWith(start, stop)

    return step


def resulting(param=None):
    return MockWith()
