import panzee.damage

def test_stats_default_values():
    stats = panzee.damage.ModelStats()
    assert stats.movement_cost == 1
    assert stats.damage_reduction == 0.0
    assert stats.max_ap == 100
    assert stats.faint_threshold == 20

def test_stats_constructor():
    stats = panzee.damage.ModelStats(
        movement_cost=3,
        damage_reduction=0.15
    )
    assert stats.movement_cost == 3
    assert stats.damage_reduction == 0.15
    assert stats.max_ap == 100


def test_model_init():
    stats = panzee.damage.ModelStats(
        movement_cost=4,
        damage_reduction=0.5,
        max_ap=75
    )
    model = panzee.damage.DamageModel(stats)
    assert model.stats.movement_cost == 4
    assert model.stats.damage_reduction == 0.5
    assert model.stats.max_ap == 75
    assert model.status == panzee.damage.STATUS_NORMAL


def test_movement_cost_calculation():
    stats = panzee.damage.ModelStats(
        movement_cost=4,
        damage_reduction=0.3
    )
    model = panzee.damage.DamageModel(stats)
    assert model.calculate_movement_cost(distance=3) == 12


def test_movement_damage():
    stats = panzee.damage.ModelStats(
        movement_cost=5,
        damage_reduction=0.25,
        max_ap=100
    )
    model = panzee.damage.DamageModel(stats)
    assert model.ap == model.stats.max_ap
    model.take_damage_for_movement(5)
    assert model.ap == 75
    assert model.status == panzee.damage.STATUS_NORMAL


def test_weapon_damage_calculation():
    stats = panzee.damage.ModelStats(
        damage_reduction=0.5
    )
    model = panzee.damage.DamageModel(stats)
    assert model.calculate_damage_taken(base_damage=30) == 15


def test_weapon_damage():
    stats = panzee.damage.ModelStats(
        damage_reduction=0.75,
        max_ap=200
    )
    model = panzee.damage.DamageModel(stats)
    assert model.ap == model.stats.max_ap
    model.take_damage(base_damage=20)
    assert model.ap == 195
    assert model.status == panzee.damage.STATUS_NORMAL


def test_status_faint():
    stats = panzee.damage.ModelStats()
    model = panzee.damage.DamageModel(stats)
    model.take_damage(85)
    assert model.ap == 15
    assert model.status == panzee.damage.STATUS_FAINTED


def test_status_dead():
    stats = panzee.damage.ModelStats()
    model = panzee.damage.DamageModel(stats)
    model.take_damage(101)
    # AP is capped at 0
    assert model.ap == 0
    assert model.status == panzee.damage.STATUS_DEAD


def test_performable_action():
    stats = panzee.damage.ModelStats()
    model = panzee.damage.DamageModel(stats)
    model.take_damage(75)
    assert model.ap == 25
    # Can't perform an action that would cause fainting
    assert model.can_perform_action_with_cost(10) == False
    assert model.can_perform_action_with_cost(3) == True
