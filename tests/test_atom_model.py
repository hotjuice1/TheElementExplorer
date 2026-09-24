import pytest
from models.atom import Atom

@pytest.mark.parametrize("symbol,isotopes",[("H",[1,2,3]),("C",[12,13,14]),("U",[234,235,238])])
def test_isotope_switching(catalog,symbol,isotopes):
    atom = Atom(catalog.lookup(symbol))
    for mass in isotopes:
        atom.set_state(mass,0)
        assert atom.neutrons == mass-atom.protons
        assert atom.electrons == atom.protons

@pytest.mark.parametrize("symbol,charge,notation,shells",[
    ("Na",1,"Na⁺",(2,8)),("Cl",-1,"Cl⁻",(2,8,8)),
    ("Fe",2,"Fe²⁺",(2,8,14)),("H",1,"H⁺",()),("O",-2,"O²⁻",(2,8))])
def test_ions(catalog,symbol,charge,notation,shells):
    atom = Atom(catalog.lookup(symbol),charge=charge)
    assert atom.electrons == atom.protons-charge
    assert atom.notation == notation
    assert atom.shells == shells

def test_all_ions_and_isotopes(catalog):
    for e in catalog.elements:
        for charge in range(-3,min(3,e.atomic_number)+1):
            atom = Atom(e,charge=charge)
            assert sum(atom.shells) == e.atomic_number-charge
        for iso in e.isotopes:
            assert Atom(e,mass_number=iso.mass_number).neutrons >= 0

@pytest.mark.parametrize("mass,charge",[(99,0),(1,2),(1,4),(1,-4),(1,1.5),(1.0,0)])
def test_rejected_changes_are_atomic(catalog,mass,charge):
    atom = Atom(catalog.lookup("H"))
    before = atom.mass_number,atom.charge,atom.subshells
    with pytest.raises(ValueError):
        atom.set_state(mass,charge)
    assert (atom.mass_number,atom.charge,atom.subshells) == before
