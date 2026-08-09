# Architectural Plan: Symbolic Expression Parsing

## Problem
The current `Combinational Logic Minimizer` relies on truth table inputs, which is inefficient and does not scale (exponential growth $O(2^n)$).

## Proposed Solution
Bypass truth table generation entirely by implementing a symbolic expression parsing pipeline, and add netlist generation.

### Steps
1. **Symbolic Parser:** Use `sympy` to convert raw user input expressions into Disjunctive Normal Form (DNF).
2. **Cube Transformer:** Map `sympy`'s DNF structure into the internal cube representation expected by the ESPRESSO algorithm (`list` of `list` of `(0,0), (0,1), (1,0)` tuples).
3. **Minimization:** Run the ESPRESSO engine.
4. **Netlist Generator:** Convert the minimized logic into a SPICE-style netlist text file using only the standard building blocks: NOT, BUFF, AND, OR, NAND, NOR, XOR, XNOR, MUX2x1. (DFF is not applicable for combinational logic).

## Benefits
- Improved performance and memory efficiency by avoiding exponential truth table generation.
- More intuitive user experience.
- Better integration with symbolic-based design flows.
- Compatibility with `Logic Simulator` via standard netlist output.
