# Architectural Plan: ROBDD-based Logic Equivalence Checker

## Feasibility
Highly feasible. ROBDDs (Reduced Ordered Binary Decision Diagrams) provide a **canonical representation** for boolean functions. For combinational logic circuits, two circuits are logically equivalent if and only if their reduced ROBDDs are identical (isomorphic). This is the standard, efficient approach for educational VLSI CAD tools.

## Proposed Architecture

### 1. Unified Input Parsing Layer
A modular parsing system that converts different input types into a standardized representation (e.g., a BDD-friendly symbolic representation or an intermediate circuit graph).
- **Truth Table (CSV):** Parse rows into boolean functions (e.g., Minterm expansion).
- **Netlist (txt):** Parse the netlist nodes using the 10 standard building blocks.
- **Expression (string):** Parse infix/postfix strings into boolean trees.

### 2. BDD Manager
Implement or integrate a BDD construction engine.
- Incremental BDD construction using `Apply` operations (AND, OR, NOT).
- Implement node sharing (memoization table) to ensure identical sub-graphs are shared.

### 3. ROBDD Reduction
Ensure the constructed BDDs satisfy the ROBDD properties:
- **Ordered:** Variables are ordered consistently across both circuits.
- **Reduced:**
    - No redundant nodes (children are identical).
    - No duplicate nodes (identical node signature).

### 4. Equivalence Comparison
- Once reduced, the root nodes of the two ROBDDs represent the boolean function.
- Equivalence is checked by comparing the root node pointers (if node sharing is strictly enforced, identity is sufficient) or performing a graph isomorphism check.

## Implementation Roadmap
1. **Parser Implementation:** Build the 3 input parsers.
2. **BDD Core:** Implement or integrate the BDD construction and reduction algorithms.
3. **Equivalence Logic:** Implement the root-comparison check.
4. **Tool-chain Integration:** Ensure inputs are compatible with other tools in the suite.

## Benefits
- **Educational Value:** Demonstrates the power of canonical data structures in CAD.
- **Performance:** Much faster than truth-table-based comparison for moderate circuit sizes.
- **Modularity:** Parsers can be reused across the entire tool-suite.
