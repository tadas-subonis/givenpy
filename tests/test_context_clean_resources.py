from dataclasses import dataclass

from givenpy import given, then, lambda_with
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
