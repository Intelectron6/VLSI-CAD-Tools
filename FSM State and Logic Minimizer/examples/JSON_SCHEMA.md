# JSON Schema for FSM Input

This document defines the JSON schema for FSM (Finite State Machine) input,
intended as an alternative to the CSV transition table format used by
`fsm_minimizer.py`.

## Schema

```json
{
  "fsm_name": "string (optional, descriptive name)",
  "initial_state": "string (optional, name of the initial/reset state)",
  "states": ["string", ...],                       // ordered list of state names
  "inputs": ["integer", ...],                      // ordered list of input values
  "transitions": [
    {
      "ps": "string",    // Present State
      "x": integer,      // Input value
      "ns": "string",    // Next State
      "z": integer       // Output value (0 or 1)
    },
    ...
  ]
}
```

### Field Details

| Field | Type | Required | Description |
|---|---|---|---|
| `fsm_name` | string | No | Human-readable name for documentation |
| `initial_state` | string | No | Name of the initial/reset state |
| `states` | array of strings | Yes | All state names in the machine |
| `inputs` | array of integers | Yes | All possible input values |
| `transitions` | array of objects | Yes | Each transition: `ps`, `x`, `ns`, `z` |

### Transition Object

| Field | Type | Description |
|---|---|---|
| `ps` | string | Present state name (must exist in `states`) |
| `x` | integer | Input value (must exist in `inputs`) |
| `ns` | string | Next state name (must exist in `states`) |
| `z` | integer | Output value (0 or 1) |

### Equivalence to CSV

The CSV format has columns: `x, PS, NS, z`. Each row is one transition.

Example CSV row:
```
0,A,E,0
```

Equivalent JSON transition:
```json
{"ps": "A", "x": 0, "ns": "E", "z": 0}
```

## Example Files

- `examples/fsm.json` — matches `fsm.csv` (6 states, inputs 0 and 1)
- `examples/fsm2.json` — matches `fsm2.csv` (6 states, inputs 0, 1, 10, 11)
