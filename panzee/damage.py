STATUS_NORMAL, STATUS_FAINTED, STATUS_DEAD = range(3)


class ModelStats(object):
	faint_threshold = 20
	action_points = 150
	def __init__(self, movement_cost=None, damage_reduction=None, max_ap=None, faint_threshold=None):
		if movement_cost is None:
			self.movement_cost = 1
		else:
			self.movement_cost = movement_cost

		if damage_reduction is None:
			self.damage_reduction = 0.0
		else:
			self.damage_reduction = damage_reduction

		if max_ap is None:
			self.max_ap = 100
		else:
			self.max_ap = max_ap

		if faint_threshold is None:
			self.faint_threshold = 20
		else:
			self.faint_threshold = faint_threshold


class DamageModel(object):

	def __init__(self, stats):
		self.stats = stats
		self.status = STATUS_NORMAL
		self.ap = self.stats.max_ap

	def calculate_movement_cost(self, distance):
		return self.stats.movement_cost * distance

	def take_damage_for_movement(self, distance):
		self.ap -= self.calculate_movement_cost(distance)

	def calculate_damage_taken(self, base_damage):
		return base_damage * (1.0 - self.stats.damage_reduction)

	def take_damage(self, base_damage):
		self.ap -= self.calculate_damage_taken(base_damage)
		if self.ap <= self.stats.faint_threshold:
			self.status = STATUS_FAINTED
		if self.ap < 0:
			self.ap = 0
		if self.ap == 0:
			self.status = STATUS_DEAD

	def can_perform_action_with_cost(self, cost):
		return not self.ap - cost <= self.stats.faint_threshold
