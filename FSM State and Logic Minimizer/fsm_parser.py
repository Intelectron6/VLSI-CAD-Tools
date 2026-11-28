"""
JSON parser for FSM input.

Converts a JSON-format FSM description into a pandas DataFrame with columns
'x', 'PS', 'NS', 'z' — the same format expected by fsm_minimizer.py's
run_minimization() function.

JSON schema (see examples/JSON_SCHEMA.md):
{
  "fsm_name": "string (optional)",
  "initial_state": "string (optional)",
  "states": ["string", ...],
  "inputs": [integer, ...],
  "transitions": [
    {"ps": "string", "x": integer, "ns": "string", "z": integer},
    ...
  ]
}
"""

import json
import pandas as pd


def json_to_dataframe(json_path):
    """Load an FSM from a JSON file and return a DataFrame.

    The returned DataFrame has columns 'x', 'PS', 'NS', 'z' in the same
    format as the CSV input used by fsm_minimizer.py.

    Parameters
    ----------
    json_path : str or pathlib.Path
        Path to the JSON file.

    Returns
    -------
    pandas.DataFrame
        DataFrame with columns ['x', 'PS', 'NS', 'z'].

    Raises
    ------
    FileNotFoundError
        If the JSON file does not exist.
    ValueError
        If the JSON is missing required fields or has invalid transitions.
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Validate required fields
    required = ['states', 'inputs', 'transitions']
    for field in required:
        if field not in data:
            raise ValueError(f"JSON missing required field: '{field}'")

    states = data['states']
    inputs = data['inputs']
    transitions = data['transitions']

    # Validate that all referenced states exist in the states list
    state_set = set(states)
    for i, t in enumerate(transitions):
        for key in ('ps', 'ns'):
            if t[key] not in state_set:
                raise ValueError(
                    f"Transition {i}: state '{t[key]}' not in 'states' list"
                )
        if t['x'] not in inputs:
            raise ValueError(
                f"Transition {i}: input '{t['x']}' not in 'inputs' list"
            )
        if t['z'] not in (0, 1):
            raise ValueError(
                f"Transition {i}: output '{t['z']}' must be 0 or 1"
            )

    # Build DataFrame rows in the same order as the JSON transitions list
    rows = []
    for t in transitions:
        rows.append({
            'x': t['x'],
            'PS': t['ps'],
            'NS': t['ns'],
            'z': t['z'],
        })

    df = pd.DataFrame(rows, columns=['x', 'PS', 'NS', 'z'])
    return df


def dataframe_to_csv(df, csv_path):
    """Write a DataFrame to a CSV file in fsm.csv format.

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame with columns ['x', 'PS', 'NS', 'z'].
    csv_path : str or pathlib.Path
        Output CSV file path.
    """
    df.to_csv(csv_path, index=False)


if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("Usage: python fsm_parser.py <json_file> [output_csv]")
        sys.exit(1)

    json_path = sys.argv[1]
    df = json_to_dataframe(json_path)
    print(df.to_string(index=False))

    if len(sys.argv) > 2:
        dataframe_to_csv(df, sys.argv[2])
        print(f"\nSaved to {sys.argv[2]}")
