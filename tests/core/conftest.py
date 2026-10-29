import pytest

from cijoe.core.misc import DEPRECATIONS_WARNED
from cijoe.core.resources import Collector


@pytest.fixture(autouse=True)
def reset_collector():
    # This fixture runs automatically before each test
    collector = Collector()
    collector.reset()


@pytest.fixture(autouse=True)
def reset_deprecations():
    DEPRECATIONS_WARNED.clear()
