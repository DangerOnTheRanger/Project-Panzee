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
