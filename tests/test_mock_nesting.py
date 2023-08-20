from givenpy import given, when, Mock
from hamcrest import *


def test_mock_nesting():
    with given():
        with when('I use "when" context') as when_mock:
            assert_that(isinstance(when_mock.non_existing_attribute, Mock))
