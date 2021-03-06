import yaml
import panzee.damage
import panzee.weapon

class Unit(object):
    name = ""
    weapons = {}
    internal_name = ""
    def __init__(self, unit_base):
        for data in yaml.load_all(unit_base): break
        self.name = data["stats"]["-name"]
        self.internal_name = data["stats"]["-internal_name"]
        for _, weapon in data["weapons"].iteritems():
            name = weapon["-name"]
            range_ = weapon["-range"]
            ammo = weapon["-ammo"]
            base_damage = weapon["-base_damage"]
            self.weapons[name] = panzee.weapon.Weapon(name, range_, ammo, base_damage)
        self._stats = panzee.damage.ModelStats(
        data["stats"]["-movement_cost"],
        data["stats"]["-damage_reduction"],
        data["stats"]["-max_actionpoints"],
        data["stats"]["-faint_threshold"])
        self._model = panzee.damage.DamageModel(self._stats)

    def take_damage(self, damage):
        self._model.take_damage(damage)

    def move(self, distance):
        self._model.take_damage_for_movement(distance)

    @property
    def max_ap(self):
        return self._stats.max_ap

    @property
    def ap(self):
        return self._model.ap

    @property
    def movement_cost(self):
        return self._stats.movement_cost

    @property
    def status(self):
        return self._model.status

    @property
    def damage_reduction(self):
        return self._stats.damage_reduction
