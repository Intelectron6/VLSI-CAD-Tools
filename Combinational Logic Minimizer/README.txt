Combinational Logic Minimizer - ESPRESSO Heuristic
===================================================

This Python program performs 2-level (SOP) combinational logic minimization
using the ESPRESSO heuristic. It accepts boolean functions either as a
truth-table CSV or as a symbolic expression string, and produces a minimized
SOP expression plus an optional SPICE-style netlist compatible with the
Logic Simulator project.

FILES
-----
espresso.py         - Core ESPRESSO engine + CLI entry point
run_minimizer.py    - Interactive TUI (prompt_toolkit + rich)
README.txt          - This file

SUB-FOLDERS
-----------
examples/           - Example truth-table CSVs and boolean expressions
verification/       - Test suites (verify_01.py through verify_04.py)

USAGE
-----

1. Interactive TUI (recommended for exploration):
     python run_minimizer.py

   Guides you through selecting input type (expression, CSV, or built-in
   example), setting a target cost, generating a netlist, saving results,
   and running the Logic Simulator on the generated netlist.

2. Command-line interface (for scripting/automation):
     python espresso.py --input logic.csv --tau 5 --output result.txt
     python espresso.py --expression "A & B | ~A & C | B & C" --tau 4 --netlist netlist.txt

   Options:
     --input     Path to truth-table CSV (default: examples/logic.csv)
     --expression Boolean expression string (overrides --input)
                  Accepted formats: A & B | ~C,  A AND B OR NOT C,
                  A.B + A.!B  (EE notation),  f = A & B | ~C
     --tau       Target cost (integer). If omitted, you are prompted.
     --output    Path to save the result text file
     --netlist   Path to save SPICE-style netlist (Logic Simulator format)

INPUT FORMATS
-------------

Truth-table CSV:
   Columns x{N-1} ... x1 x0, f. Cell values: 0, 1, or x (don't-care).
   Example: examples/logic.csv

Boolean expression:
   Variables: single letters A-Z (auto-detected, sorted alphabetically)
   Operators: & | ~  (AND OR NOT),  AND OR NOT  (word ops, case-insensitive),
              . + !   (EE notation: A.B + !A.C)
   Prefix:      Optional 'f = ' or 'F = '
   Examples:    A & B | ~A & C | B & C
                A.B + A.!B
                !(A.B)
                f = A & B | ~C

OUTPUT
------
Minimized SOP expression and final cost are printed to stdout.
With --output, the result is also saved to a text file.
With --netlist, a SPICE-style netlist is generated using only gates
supported by the Logic Simulator: NOT, BUFF, AND, OR, NAND, NOR, XOR,
XNOR, MUX2x1 (no DFF -- combinational only).

NETLIST FORMAT (Logic Simulator compatible):
   input x[0] x[1] ...
   output f
   AND x[0] x[1] n1
   OR n1 n2 f

EXAMPLES
--------
See the examples/ folder for truth-table CSVs and the verification/
folder for end-to-end test suites.

DEPENDENCIES
------------
numpy, pandas, sympy, random, prompt_toolkit, rich
