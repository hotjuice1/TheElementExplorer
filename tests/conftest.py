import pytest
from data.element_loader import ElementCatalog, load_elements

@pytest.fixture(scope="session")
def catalog():
    return ElementCatalog(load_elements())
