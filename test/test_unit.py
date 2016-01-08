import panzee.unit
import panzee.damage


def test_load():
    unit = panze.unit.Unit(unit_base=open("example_unit.udl").read())
    assert unit.max_ap == 150
    assert unit.ap == 150
    assert unit.status == panzee.damage.STATUS_NORMAL
    assert unit.name == "An example unit"
    assert unit.internal_name == "example"
    assert "standard_rifle" in unit.weapons
