# Scientific Units and Physical Quantities

SI-based unit definitions, physical quantities, dimensional compatibility, and conversions.

## Supported Units

| Category | Units |
|---|---|
| Length | m, km, cm |
| Time | s, min, h |
| Mass | kg, g |
| Velocity | m/s, km/h |
| Acceleration | m/s^2 |
| Force | N |
| Energy | J |

## Public API

- Unit: immutable unit definition.
- Quantity: immutable value and unit.
- get_unit(): resolves registered units.
- is_compatible(): checks physical dimensions.
- convert(): converts compatible quantities.

## Limitations

No compound-unit parser, automatic unit algebra, or uncertainty propagation. Educational foundation only; not flight-qualified software.
