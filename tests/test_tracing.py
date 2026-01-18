from givenpy import given, when, then
from hamcrest import *


def magic_function(x, external_number, another_number):
    return x + 1 + external_number + another_number


def there_is_external_number(number):
    def step(context):
        context.external_number = number

    return step

def there_is_another_number(number):
    def step(context):
        context.another_number = number

    return step


def test_magic_function_2():
    with given([
        there_is_external_number(5),
        there_is_another_number(10),
    ], trace=True) as context:
        with when("I call the magic function"):
            result = magic_function(1, context.external_number, context.another_number)

        with when("I make another call"):
            result2 = magic_function(2, context.external_number, context.another_number)

        with then("it should return correct values"):
            assert_that(result, is_(equal_to(17)))
            assert_that(result2, is_(equal_to(18)))
