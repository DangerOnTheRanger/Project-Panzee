STATUS_NORMAL = "Good"
class ModelStats:
	faint_threshold = 20 #This is a static variable, because it has been defined outside of any function in this class
	ap = 150 #actionpoints
	def __init__(self, movement_cost=None, damage_reduction=None, ma=None, ft=None):
		if movement_cost is None: # Have to be carful about have a 'arg' the same name as a class instance variable
			self.movement_cost = 1
		else:
			self.movement_cost = movement_cost

		if damage_reduction is None:
			self.damage_reduction = 0.0
			#     ^ this is a class instance variable, because it has been defined as an atribute of 'self' meaning the class instance that is this function
		else:
			self.damage_reduction = damage_reduction

		if ma is None:
			self.max_ap = 100
			# max_ap = 100
			# ^ this is a local variable and will not work for the case, since local variables are deleted after the function it's been declared in exits/ends
		else:
			self.max_ap = ma

		if ft is None:
			self.ma = 20
		else:
			self.faint_threshold = ft
