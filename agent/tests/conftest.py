import pytest
import respx as _respx


@pytest.fixture
def respx_mock():
    with _respx.mock(assert_all_called=False) as mock:
        yield mock
