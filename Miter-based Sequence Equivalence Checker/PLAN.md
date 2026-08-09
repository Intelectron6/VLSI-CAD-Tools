# Architectural Plan: Miter-based Sequence Equivalence Checker

## Feasibility
Highly feasible. Comparing two sequential circuits (FSMs) by constructing a "miter" (or product FSM) is the standard approach for sequential equivalence checking (SEC).
- Two FSMs are equivalent if all reachable states in their product machine satisfy the equivalence property (outputs are identical for all inputs).
- A counter-example is a sequence of inputs that drives the product FSM to a state where outputs differ.

## Proposed Architecture

### 1. Unified Input Parsing Layer
A modular parsing system (reused from FSM and Combinational tools) to standardize input formats into transition models.
- **State Table (CSV):** Parse transition/output tables.
- **Symbolic (JSON):** Parse state-based transition/output definitions.
- **Netlist (txt):** Extract state bits, next-state logic, and output logic.

### 2. Transition Model Extractor
A common module that takes any input format and produces a standard representation:
- State list, Input set, Output set.
- Next-State functions: $\delta(S, I) \rightarrow S'$.
- Output functions: $\lambda(S, I) \rightarrow O$.

### 3. Miter Constructor (Product FSM)
Constructs the product FSM $(M_1 \times M_2)$:
- **State Space:** The Cartesian product $S_1 \times S_2$.
- **Next-State Logic:** $\delta_{prod}((s_1, s_2), i) = (\delta_1(s_1, i), \delta_2(s_2, i))$.
- **Output Miter Logic:** $Output_{miter} = \lambda_1(s_1, i) \oplus \lambda_2(s_2, i)$. (Mismatches when output is 1).

### 4. Equivalence Solver (BFS)
Explores the reachable state space of the product FSM starting from the reset state $(s_{1,reset}, s_{2,reset})$.
- If BFS reaches a state where $Output_{miter} = 1$, flag non-equivalence and backtrack the BFS tree to produce the counter-example input sequence.
- If all reachable states are exhausted without mismatch, FSMs are equivalent.

## Implementation Roadmap
1. **Parser/Extractor:** Implement the unified FSM input handling.
2. **Miter Engine:** Build the product FSM logic using the 10 standard building blocks.
3. **BFS Solver:** Implement the state space traversal algorithm.
4. **Integration:** Link with the suite’s netlist format.

## Benefits
- **Educational Value:** Clearly demonstrates FSM equivalence, state-space exploration, and counter-example generation.
- **Diagnostic Feedback:** Provides an actionable counter-example input sequence upon mismatch.
- **Modularity:** Reuses existing parsing and logic building blocks.
