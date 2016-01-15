class ModelStats:
	faint_threshold = 20 #This is a static variable, because it has been defined outside of any function in this class
	def __init__(self, movement_cost=None, dr=None, ma=None, ft=None):
		if movement_cost is None: # Have to be carful about have a 'arg' the same name as a local variable
			self.movement_cost = 1
		else:
			self.movement_cost = movement_cost
			
		if dr is None:
			self.damage_reduction = 0.0
			#     ^ this is a local variable, because it has been defined as an atribute of 'self' meaning the instance that is currently running the function
		else:
			self.damage_reduction = dr
		
		if ma is None:
			self.max_ap = 100
			# max_ap = 100
			# ^ this will not work, for that after this function is done, the variable will be deleted
		else:
			self.max_ap = ma
		
		if ft is None:
			self.ma = 20
		else:
			self.faint_threshold = ft
		