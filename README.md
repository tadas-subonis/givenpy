# GivenPy

GivenPy is a super simple yet highly extensible micro testing library to
enable easier behavior driven development in Python.

## Example

```python
import unittest
from typing import Dict

from hamcrest import *
from starlette.testclient import TestClient

from tests.givenpy import given, when, then
from tests.steps import prepare_api_server, create_test_client, prepare_injector


class TestExample(unittest.TestCase):
    def test_health_works(self):
        with given([
            prepare_injector(),  # custom code to prepare the test environment
            prepare_api_server(),
            create_test_client(),
        ]) as context:
            client: TestClient = context.client

            with when():
                response: Dict = client.get('/api/v1/health').json()

            with then():
                assert_that(response, instance_of(dict))
                assert_that(response['status'], is_(equal_to('OK')))
```

or simpler

```python
import unittest
from typing import Dict

from hamcrest import *
from starlette.testclient import TestClient

from tests.givenpy import given, when, then
from tests.steps import prepare_api_server, create_test_client, prepare_injector


def test_health_works():
    with given([
        prepare_injector(),  # custom code to prepare the test environment
        prepare_api_server(),
        create_test_client(),
    ]) as context:
        client: TestClient = context.client

        with when():
            response: Dict = client.get('/api/v1/health').json()

        with then():
            assert_that(response, instance_of(dict))
            assert_that(response['status'], is_(equal_to('OK')))
```

## Installation

```bash
pip install givenpy PyHamcrest
```

## Documentation

```python

def magic_function(x, external_number):
    return x + 1 + external_number
    
def there_is_external_number():
    context.external_number = 1
    

def test_magic_function():
    with given([
        there_is_external_number,
    ]) as context:

        with when("I call the magic function"):
            result = magic_function(1, context.external_number)

        with then():
            assert_that(result, is_(equal_to(3)))
```

But I recommend using more flexible higher functiosn that can become configurable:

```python
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
```