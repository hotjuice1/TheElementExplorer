import json
import pytest
from data.element_loader import DATA_PATH, load_elements
from models.electron_shell import parse_configuration, shell_populations

def test_completeness(catalog):
    assert len(catalog.elements) == 118
    assert set(catalog.by_number) == set(range(1,119))
    assert len({e.symbol for e in catalog.elements}) == 118
    for element in catalog.elements:
        shells = shell_populations(parse_configuration(element.electron_configuration))
        assert sum(shells) == element.atomic_number == element.electrons == element.protons
        assert element.shell_distribution == shells
        assert element.neutrons >= 0

@pytest.mark.parametrize("query",["Au","gold","GOLD","79","  Au  "])
def test_lookup(catalog,query):
    assert catalog.lookup(query).atomic_number == 79

@pytest.mark.parametrize("query",["", "xyz", "119", "-1", "[]", "🥨"])
def test_invalid_search(catalog,query):
    assert catalog.lookup(query) is None

def test_combined_filters(catalog):
    assert [e.symbol for e in catalog.search(category="noble gas",period=3,block="p")] == ["Ar"]
    assert catalog.search("gold",period=1) == []
    assert len(catalog.search(block="f")) == 30

def test_known_physical_units(catalog):
    assert catalog.lookup("H").density == pytest.approx(.00008988)
    assert catalog.lookup("Au").density == pytest.approx(19.3)
    assert catalog.lookup("C").atomic_radius == pytest.approx(76)
    assert catalog.lookup("Og").state == "unknown"

@pytest.mark.parametrize("damage",["count","number","symbol","shell","neutrons","isotopes","configuration","missing","category","density","type"])
def test_invalid_dataset(tmp_path,damage):
    rows = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    if damage == "count": rows.pop()
    elif damage == "number": rows[1]["atomic_number"] = 1
    elif damage == "symbol": rows[1]["symbol"] = "H"
    elif damage == "shell": rows[0]["shell_distribution"] = [2]
    elif damage == "neutrons": rows[0]["neutrons"] = -1
    elif damage == "isotopes": rows[0]["isotopes"] = []
    elif damage == "configuration": rows[0]["electron_configuration"] = "1s3"
    elif damage == "missing": del rows[0]["symbol"]
    elif damage == "category": rows[0]["category"] = "invalid"
    elif damage == "density": rows[0]["density"] = "not-a-number"
    elif damage == "type": rows[0]["atomic_number"] = 1.0
    path = tmp_path/"elements.json"
    path.write_text(json.dumps(rows),encoding="utf-8")
    with pytest.raises(ValueError,match="Cannot load element data"):
        load_elements(path)

def test_broken_json(tmp_path):
    path = tmp_path/"bad.json"
    path.write_text("{",encoding="utf-8")
    with pytest.raises(ValueError,match="Cannot load element data"):
        load_elements(path)
