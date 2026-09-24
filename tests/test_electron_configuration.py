import pytest
from models.electron_shell import parse_configuration, shell_populations, format_configuration

@pytest.mark.parametrize("text",["1s3","2p7","1p1","[Qq] 2s1","1s2 garbage","1s2 1s1","[He] 1s1","", "3d-1"])
def test_invalid_configuration(text):
    with pytest.raises(ValueError):
        parse_configuration(text)

def test_notation_and_core():
    parsed = parse_configuration("[Ne] 3s² 3p⁶")
    assert shell_populations(parsed) == (2,8,8)
    assert "3p⁶" in format_configuration(parsed)
    assert format_configuration(parsed) == "1s² 2s² 2p⁶ 3s² 3p⁶"

@pytest.mark.parametrize("symbol,expected",[
    ("Cr",(2,8,13,1)), ("Cu",(2,8,18,1)), ("Nb",(2,8,18,12,1)),
    ("Mo",(2,8,18,13,1)), ("Ru",(2,8,18,15,1)), ("Rh",(2,8,18,16,1)),
    ("Pd",(2,8,18,18)), ("Ag",(2,8,18,18,1)),
    ("Pt",(2,8,18,32,17,1)), ("Au",(2,8,18,32,18,1)),
    ("Lr",(2,8,18,32,32,8,3)), ("Og",(2,8,18,32,32,18,8))])
def test_ground_state_exceptions(catalog,symbol,expected):
    assert shell_populations(parse_configuration(catalog.lookup(symbol).electron_configuration)) == expected
