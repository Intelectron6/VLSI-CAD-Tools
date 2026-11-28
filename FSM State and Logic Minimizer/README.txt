FSM State and Logic Minimizer
=============================

This Python program performs FSM state minimization and output/next state logic
minimization using the ESPRESSO heuristic. It accepts state transition tables
specified in CSV or JSON format as input.

Equivalence checking is performed to reduce the number of essential states in
the FSM. ESPRESSO heuristic is used to minimize the next state logic and
output logic functions of the FSM.

The tool provides the following outputs:
-> Output logic in terms of inputs and present state
-> Next state logic in terms of inputs and present state
-> Critical path delay (i.e. worst case delay among all the logic functions found)
-> SPICE-style netlist compatible with the Logic Simulator (via fsm_netlist.py)
-> Interactive TUI for guided usage (via run_fsm_minimizer.py)

State transition diagrams (via fsm_diagram.py) are implemented but
temporarily disabled in the TUI due to arrow rendering issues.
They will be re-enabled in a future update.

FILES
-----
fsm_minimizer.py   - Core FSM state minimization + ESPRESSO logic minimization
                     (importable module with run_minimization() function)
fsm_parser.py      - JSON parser: converts JSON FSM input to DataFrame format
fsm_netlist.py     - Netlist generator: creates SPICE-style netlist from
                     minimization results
fsm_diagram.py     - State transition diagram generator (initial + reduced)
run_fsm_minimizer.py - Interactive TUI (prompt_toolkit + rich)
PLAN.md            - Architectural plan for future enhancements
README.txt         - This file

SUB-FOLDERS
-----------
examples/          - Example input files (CSV and JSON)
verification/      - Test suites (verify_json_csv_parity.py)

USAGE
-----

1. Interactive TUI (recommended):
     python run_fsm_minimizer.py

2. Run directly (CSV input, interactive):
     python fsm_minimizer.py

3. Use as a module (CSV or JSON input):
     from fsm_minimizer import run_minimization
     import pandas as pd
     stt_df = pd.read_csv('examples/fsm.csv')
     result = run_minimization(stt_df, target_cost=5)

   Or from JSON:
     from fsm_parser import json_to_dataframe
     from fsm_minimizer import run_minimization
     stt_df = json_to_dataframe('examples/fsm.json')
     result = run_minimization(stt_df, target_cost=5)

4. Generate netlist:
     python fsm_netlist.py examples/fsm.csv 5 fsm_netlist.txt
     python fsm_netlist.py examples/fsm.json 5 fsm_netlist.txt

5. Generate state transition diagrams (standalone, temporarily disabled in TUI):
     python fsm_diagram.py examples/fsm.csv fsm_diagrams
     python fsm_diagram.py examples/fsm.json fsm_diagrams pdf

INPUT FORMATS
-------------

CSV format:
   Columns: x, PS, NS, z
   - x: input value (decimal, treated as binary-coded)
   - PS: present state name
   - NS: next state name
   - z: output value (0 or 1)
   Example: examples/fsm.csv

JSON format:
   See examples/JSON_SCHEMA.md for the full schema.
   Example: examples/fsm.json

   {
     "fsm_name": "string (optional)",
     "initial_state": "string (optional)",
     "states": ["A", "B", "C", ...],
     "inputs": [0, 1, ...],
     "transitions": [
       {"ps": "A", "x": 0, "ns": "E", "z": 0},
       ...
     ]
   }

NETLIST FORMAT (Logic Simulator compatible)
--------------------------------------------
   INPUTS x[0] clk rst
   OUTPUTS z[0] PS[0] PS[1]
   NOT x[0] n1
   AND n1 PS[0] n2
   ...
   DFF NS[0] clk rst PS[0]
   DFF NS[1] clk rst PS[1]

   Uses gates: NOT, BUFF, AND, OR, NAND, NOR, XOR, XNOR, MUX2x1, DFF

DEPENDENCIES
------------
numpy, pandas, random, prompt_toolkit, rich

Optional (for state transition diagrams - disabled in TUI for now):
graphviz, matplotlib, networkx
