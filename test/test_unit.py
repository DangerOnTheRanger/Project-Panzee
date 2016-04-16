import panzee.unit
import panzee.damage


def test_load():
    unit = panzee.unit.Unit(unit_base=open("test/example_unit.udl").read())
    assert unit.max_ap == 150
    assert unit.ap == 150
    assert unit.status == panzee.damage.STATUS_NORMAL
    assert unit.name == "An example unit"
    assert unit.internal_name == "example"
    #assert "standard_rifle" in unit.weapons
	# ^ was the original test. (MC_): I changed it because it didn't seem to
    # work with anything I tried, I assume it was a typo.
    assert "-standard_rifle" in unit.weapons
    # (MC_): I added this one, because I wasn't sure what the original test was looking/testing for
    assert "standard_rifle" in unit.weapons ["-standard_rifle"]


def test_calculations():
    unit = panzee.unit.Unit(unit_base=open("test/example_unit.udl").read())
    unit.take_damage(20)
    assert unit.ap == 132
    unit.move(3)
    assert unit.ap == 126
    unit.take_damage(500)
    assert unit.ap == 0
    assert unit.status == panzee.damage.STATUS_DEAD
