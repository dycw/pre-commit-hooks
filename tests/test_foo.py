import datetime
from abc import abstractmethod

from pytest import mark


@mark.xfail(reason="arst", until=datetime.date(2021, 4, 4))
def test_main() -> None:
    x = 4
    assert x > 0


class Foo:
    @abstractmethod
    def foo(self, a: int) -> int:
        raise NotImplementedError
