[![PyPI](https://img.shields.io/pypi/v/givenpy.svg)](https://pypi.org/project/givenpy/)
[![Build](https://github.com/tadas-subonis/givenpy/actions/workflows/publish-to-pypi.yml/badge.svg)](https://github.com/tadas-subonis/givenpy/actions/workflows/publish-to-pypi.yml)

# GivenPy

GivenPy is a super simple yet highly extensible micro testing library to
enable easier behavior driven development in Python.

It doesn't require any fancy dependencies and can work with any test execution framework like unittest or pytest.

It is basically a syntax sugar that allows you to write tests in a more readable way. It also helps you
to encourage the re-use of setup code (given steps).

## Examples

A quick preview of what you can do with GivenPy:

```python
import unittest
from typing import Dict

from givenpy import given, when, then
from hamcrest import *
from starlette.testclient import TestClient

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

## Installation

```bash
pip install givenpy PyHamcrest
```

## Documentation

```python
from givenpy import given, when, then
from hamcrest import *


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
```

You can also set up cleanup steps that will be executed after the test is finished:

```python
from dataclasses import dataclass

from givenpy import given, when, then, lambda_with
from hamcrest import *


@dataclass
class Database:
    connected: bool = False

    def connect(self):
        self.connected = True

    def disconnect(self):
        self.connected = False


def database_is_ready():
    def step(context):
        def open():
            context.database = Database()
            context.database.connect()

        def close():
            context.database.disconnect()

        return lambda_with(open, close)

    return step


def test_database_should_be_closed_when_we_exit_context():
    with given([
        database_is_ready(),
    ]) as context:
        with then("it should connect to the database"):
            assert_that(context.database.connected, is_(True))

    with then("when context closes, it should disconnect from the database"):
        assert_that(context.database.connected, is_(False))
```

## Guidelines

- Always be explicit with your environment set up by adding all the necessary steps to the `given` block.
    - Make the setup steps as simple as possible. You can create master steps that will call other steps.
- Always prefer higher-order functions over simple functions for setup steps. This will allow you to create more
  flexible steps by allowing to parametrize them later.
- The test should always have given, when and then blocks.
- The test name should describe a functional behavior and should give an overview of what's happening and what are the
  expectations.
    - For example: `test_user_should_be_able_to_login`
      or `test_user_should_not_be_able_to_login_with_invalid_credentials`
    - And not: `test_login` or `test_invalid_credentials`
- The test should be readable and should not require any additional comments to understand what's happening.
- There should be only one `when` block per test. If you need multiple blocks, then you probably need multiple tests.
- The `when` block should be as simple as possible. It should only contain the code that is being tested. Test the code
  from the end-user perspective.
- Use PyHamcrest to write assertions. It's much more readable than the default unittest assertions.
    - Do not be afraid to introduce [custom matchers](https://pyhamcrest.readthedocs.io/en/release-1.8/custom_matchers/)
      if needed.
    - Extract complex & nested matchers to behavior-named functions that return the final matcher.

## More examples

This example is from one of the bigger projects where we use givenpy to test our API endpoints.

```python

import logging

import ulid
from hamcrest import *
from starlette.testclient import TestClient

from app.organizations.repository import TeamRepository
from app.organizations.team.core import Team
from givenpy import given, when, then
from tests.integration.organization.test_feedback_submission import person_is_present
from tests.integration.steps_auth import auth_is_ready
from tests.integration.steps_database import database_repo_is_ready, database_is_clean
from tests.integration.steps_issues import there_is_organization
from tests.steps import prepare_api_server, create_test_client, prepare_injector

logging.basicConfig(level=logging.DEBUG)


def test_team_creation_for_the_organization_should_work():
    with given([
        prepare_injector(),
        database_repo_is_ready(),
        database_is_clean(),
        prepare_api_server(),
        there_is_organization(),
        create_test_client(),
        auth_is_ready(),
    ]) as context:
        client: TestClient = context.client
        organization_id: ulid.ULID = context.organization_id

        with when():
            payload = {
                "command_name": "CreateTeamCommand",
                "entity_type": "team",
                "payload": {
                    "name": "Test Team",
                    "organization_id": str(organization_id),
                    "members": [
                    ]
                }
            }

            response = client.post(
                f'/api/v1/organizations/{organization_id}/teams',
                headers=context.add_token(),
                json=payload
            )

        with then():
            assert_that(response.status_code, equal_to(200))

            team_repo: TeamRepository = context.injector.get(TeamRepository)
            team = team_repo.find_one(response.json()['id'])

            assert_that(team.name, equal_to("Test Team"))
            assert_that(team.organization_id, equal_to(organization_id))


def there_is_team(name="Test Team"):
    def step(context):
        team_repo: TeamRepository = context.injector.get(TeamRepository)
        team = team_repo.save(
            Team(
                name=name,
                organization_id=context.organization_id,
                id=ulid.new(),
            )
        )
        context.team_id = team.id

    return step


def test_i_should_be_able_to_add_the_person_to_a_team():
    with given([
        prepare_injector(),
        database_repo_is_ready(),
        database_is_clean(),
        prepare_api_server(),
        there_is_organization(),
        create_test_client(),
        person_is_present(),
        there_is_team("Test Team 1"),
        auth_is_ready(),
    ]) as context:
        client: TestClient = context.client
        organization_id: ulid.ULID = context.organization_id
        team_repo: TeamRepository = context.injector.get(TeamRepository)

        with when():
            payload = {
                "command_name": "AddPersonToTeamCommand",
                "entity_type": "team",
                "payload": {
                    "team_id": str(context.team_id),
                    "person_id": str(context.person_id),
                }
            }

            response = client.post(
                f'/api/v1/organizations/{organization_id}/teams/{context.team_id}',
                headers=context.add_token(),
                json=payload
            )

        with then():
            team = team_repo.find_one(context.team_id)

            assert_that(response.status_code, equal_to(200))
            assert_that(team.people, has_item(context.person_id))


def test_a_list_of_teams_for_the_current_organization_should_be_retrievable():
    with given([
        prepare_injector(),
        database_repo_is_ready(),
        database_is_clean(),
        prepare_api_server(),
        there_is_organization(),
        create_test_client(),
        person_is_present(),
        there_is_team(name="Test Team 1"),
        there_is_team("Test Team 1"),
        auth_is_ready(),
    ]) as context:
        client: TestClient = context.client
        organization_id: ulid.ULID = context.organization_id

        with when():
            response = client.get(
                f'/api/v1/organizations/{organization_id}/teams',
                headers=context.add_token(),
            )

        with then():
            assert_that(response.json(), has_length(2))

```

# Contributing

Just create a PR or something. I'll review it and merge it if it's good.

## Releasing a new version

```bash
git tag -a 1.0.2 -m "Tag 1.0.2"
git push 
git push origin --tags
```