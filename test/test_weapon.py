import panzee.weapon


def test_params():
    gun = panzee.weapon.Weapon("AK-47", range_=3, ammo=10, base_damage=50)
    assert gun.name == "AK-47"
    assert gun.range == 3
    assert gun.ammo == 10
    assert gun.base_damage == 50
