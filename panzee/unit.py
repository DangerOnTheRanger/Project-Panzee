import yaml
import panzee.damage

class Unit(panzee.damage.ModelStats):
	name = "An example unit"
	weapons = ""
	status = panzee.damage.STATUS_NORMAL
	internal_name = "example"
	def __init__(self,unit_base=None):
		if(unit_base==None):
			print "Nothing to see here"
		else:
			for data in yaml.load_all(unit_base):
				break
			self.max_ap = data["stats"]["-max_actionpoints"]
			self.movement_cost = data["stats"]["-movement_cost"]
			self.damage_reduction = data["stats"]["-damage_reduction"]
			self.faint_threshold = data["stats"]["-faint_threshold"]
			self.weapons = data["weapons"]