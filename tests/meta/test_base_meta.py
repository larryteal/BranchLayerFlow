from pydantic import ValidationError
from branchlayerflow import BaseMeta
import pytest

@pytest.fixture
def meta():
    return BaseMeta(**{ "name": "meta" })

def test_initial_value():
    m = BaseMeta(**{ "name": "m" })
    assert m.name == "m"

def test_extra_allow():
    x = BaseMeta(**{ "name": "m", "test": True })
    assert x.test == True # type: ignore

def test_frozen(meta):
    with pytest.raises(ValidationError):
        meta.name = ""
