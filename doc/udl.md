Unit Description Language
=========================

Project Panzee's Unit Description Language (UDL) is used to specify individual
unit's abilities, stats, and so on. UDL uses YAML as the underlying data format,
to both enhance readability and to avoid reinventing the wheel.

An example of a valid UDL file would be:
```
stats:
  -name: An example unit
  -internal_name: example
  -desc: |
    An example unit, used for describing Project Panzee's UDL.
    Not a whole lot to this one, as it's intentionally bare-bones to only
    provide a very brief overview of what a valid UDL file would look like.
  -max_actionpoints: 150
  -damage_reduction: 0.10
  -faint_threshold: 15
  -movement_cost: 2
  -type: faction
weapons:
  -standard_rifle
  -custom_weapon
  -custom_expendable_weapon
    ammo: 5
```

* `name` represents the exterior name of the unit visible to the end-user.
* `internal_name` represents the name used internally inside the game engine to refer
  to this unit.
* `desc` is a human-readable overview of this unit.
* `max_actionpoints` is an integer representing the maximum AP this unit can hold.
* `damage_reduction` is a floating point number detailing the base damage reduction
  of this unit - in the above case, 10%.
* `faint_threshold` is maximum AP level that the unit can have before fainting.
* `movement_cost` represents the AP cost per tile that the unit will suffer
  while moving.
* `type` specifies the type of the unit. Valid values are `faction` (a globally-available
  unit) and `merc`, i.e, a draftable unit.
* `weapons` is a sequence specifying what weapons are available to this unit.
