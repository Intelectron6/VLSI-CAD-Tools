# Architectural Plan: Symbolic FSM Input & Decoupled Minimization

## Problem
The current `FSM State and Logic Minimizer` is monolithic—it combines state minimization and logic synthesis—and relies on rigid, error-prone CSV input for transition tables. This limits both pedagogical clarity and tool-chain flexibility.

## Proposed Solution
1. **Symbolic Input:** Adopt a JSON-based FSM representation to replace the CSV transition table.
2. **Decoupled Flow:** Separate the state minimization and logic minimization phases into distinct, chainable steps.
3. **Netlist Generator:** Generate SPICE-style netlists for the minimized logic using the standard building blocks: NOT, BUFF, AND, OR, NAND, NOR, XOR, XNOR, MUX2x1, DFF.

## Implementation Steps
1. **JSON Schema Definition:** Define a clear JSON structure representing the FSM:
   - States
   - Input symbols
   - Transitions (`{CurrentState, Input} -> {NextState, Output}`)
2. **JSON Parser:** Implement a parser to load this JSON and generate the internal transition/output tables required by the state minimizer.
3. **Refactoring `fsm_minimizer.py`:**
   - **Phase 1: State Minimization:** Extract the state minimization algorithm into a modular function that takes the parsed FSM and returns an optimized (equivalent) FSM object/structure.
   - **Phase 2: Logic Minimization:** Extract the logic synthesis part into a separate function/module that takes the optimized FSM and applies the ESPRESSO heuristic (using the logic developed for the Combinational Minimizer).
   - **Phase 3: Netlist Generation:** Convert the final minimized next-state and output logic into a netlist using the 10 building blocks.
4. **Integration:** Create a main pipeline function that optionally allows running the full flow or individual phases.

## Benefits
- **Modularity:** Students can analyze the effect of state minimization independently of logic synthesis.
- **Usability:** Symbolic JSON input is easier to write, read, and validate than large CSV tables.
- **Extensibility:** Easier to integrate into larger tool-chains (e.g., feeding an optimized state machine into a different synthesis tool).
- **Compatibility:** Output netlists can be directly simulated in the `Logic Simulator`.
