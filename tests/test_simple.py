from givenpy import given, when, then
from hamcrest import *


def magic_function(x, external_number):
    return x + 1 + external_number


def there_is_external_number(number):
    def step(context):
        context.external_number = number

    return step


def test_magic_function():
    with given([
        there_is_external_number(5),
    ]) as context:
        with when("I call the magic function"):
            result = magic_function(1, context.external_number)

        with then("it should return 7"):
            assert_that(result, is_(equal_to(7)))
