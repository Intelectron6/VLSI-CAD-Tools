"""
Netlist generator for FSM Minimizer.

Converts minimized FSM logic (from fsm_minimizer.run_minimization())
into a SPICE-style netlist compatible with the Logic Simulator.

Supports: NOT, BUFF, AND, OR, NAND, NOR, XOR, XNOR, MUX2x1, DFF

Usage:
    python fsm_netlist.py <csv_or_json_file> [target_cost] [output_netlist]

Examples:
    python fsm_netlist.py fsm.csv 5 fsm_netlist.txt
    python fsm_netlist.py examples/fsm.json 5 fsm_netlist.txt
"""

import re
import math
import sys
import os
from pathlib import Path

# Add the FSM directory to path so we can import fsm_minimizer and fsm_parser
FSM_DIR = os.path.dirname(os.path.abspath(__file__))
if FSM_DIR not in sys.path:
    sys.path.insert(0, FSM_DIR)

import pandas as pd

from fsm_minimizer import run_minimization


def split_top_level(s, sep):
    """Split string by separator at top level (not inside parentheses).

    Example: split_top_level('(A AND B) OR (C AND D)', ' OR ')
             -> ['(A AND B)', '(C AND D)']
    """
    parts = []
    current = ''
    depth = 0
    i = 0
    sep_len = len(sep)
    while i < len(s):
        if s[i] == '(':
            depth += 1
            current += s[i]
            i += 1
        elif s[i] == ')':
            depth -= 1
            current += s[i]
            i += 1
        elif depth == 0 and s[i:i + sep_len] == sep:
            parts.append(current.strip())
            current = ''
            i += sep_len
        else:
            current += s[i]
            i += 1
    if current.strip():
        parts.append(current.strip())
    return parts


def parse_sop_terms(expr_str):
    """Parse a minimized SOP expression into a list of terms.

    Each term is a list of literals. Each literal is (var_name, is_negated).
    Expression format: '((NOT x[0]) AND x[1]) OR (x[0] AND x[2])'

    Variable names are preserved as-is (e.g. 'x[0]', 'PS[1]').
    """
    s = re.sub(r'^[fF]\s*=\s*', '', expr_str.strip())

    # Split by top-level OR
    terms_str = split_top_level(s, ' OR ')

    terms = []
    for term_str in terms_str:
        term_str = term_str.strip()

        # Strip outer parentheses (may be nested)
        while term_str.startswith('(') and term_str.endswith(')'):
            inner = term_str[1:-1]
            depth = 0
            balanced = True
            for ch in inner:
                if ch == '(':
                    depth += 1
                elif ch == ')':
                    depth -= 1
                    if depth < 0:
                        balanced = False
                        break
            if depth == 0 and balanced:
                term_str = inner.strip()
            else:
                break

        # Split by top-level AND
        literals_str = split_top_level(term_str, ' AND ')

        literals = []
        for lit_str in literals_str:
            lit_str = lit_str.strip()

            # Strip parentheses around negated literals: (NOT x[0]) -> NOT x[0]
            while lit_str.startswith('(') and lit_str.endswith(')'):
                lit_str = lit_str[1:-1].strip()

            if lit_str.startswith('NOT '):
                var_name = lit_str[4:].strip()
                is_negated = True
            else:
                var_name = lit_str
                is_negated = False

            literals.append((var_name, is_negated))

        terms.append(literals)

    return terms


def _get_inp_len_from_expressions(expressions):
    """Infer number of input bits from x[N] references in expressions.

    Used as fallback if result dict doesn't contain 'inp_len'.
    """
    max_idx = -1
    for expr in expressions:
        for m in re.finditer(r'x\[(\d+)\]', expr):
            idx = int(m.group(1))
            max_idx = max(max_idx, idx)
    return max_idx + 1 if max_idx >= 0 else 0


def generate_fsm_netlist(result, output_node_prefix='z',
                         state_node_prefix='PS',
                         next_state_node_prefix='NS',
                         input_node_prefix='x',
                         netlist_path='fsm_netlist.txt',
                         clock_node='clk', reset_node='rst'):
    """Generate a SPICE-style netlist from FSM minimization results.

    The netlist uses only gates supported by the Logic Simulator:
    NOT, BUFF, AND, OR, NAND, NOR, XOR, XNOR, MUX2x1, DFF.

    Structure:
      Line 1: INPUTS  x[0] x[1] ... clk rst
      Line 2: OUTPUTS z[0] z[1] ... PS[0] PS[1] ...
      Lines 3+: gate definitions (combinational logic + DFFs)

    Each next-state bit NS[i] is computed by combinational logic from
    x[N] and PS[N] inputs. Each NS[i] feeds the D input of DFF i,
    whose Q output is PS[i] (present state).

    Parameters
    ----------
    result : dict
        Result dict from fsm_minimizer.run_minimization() with keys:
        - 'expressions': list of minimized SOP expression strings
        - 'final_states': list of minimized state names
        - 'transition_table': DataFrame
        - 'costs': list of costs
        - 'max_cost': maximum cost across all outputs
    output_node_prefix : str
        Prefix for primary output nodes (default: 'z')
    state_node_prefix : str
        Prefix for present state nodes (default: 'PS')
    next_state_node_prefix : str
        Prefix for next state nodes (default: 'NS')
    input_node_prefix : str
        Prefix for input nodes (default: 'x')
    netlist_path : str
        Output netlist file path
    clock_node : str
        Clock signal name (default: 'clk')
    reset_node : str
        Reset signal name (default: 'rst')

    Returns
    -------
    str
        The generated netlist text
    """
    expressions = result['expressions']
    final_states = result['final_states']
    transition_table = result['transition_table']

    # Determine number of state bits
    num_states = len(final_states)
    if num_states <= 1:
        st_len = 1
    else:
        st_len = math.ceil(math.log2(num_states))

    # Count input bits from result dict (computed during minimization)
    inp_len = result.get('inp_len', _get_inp_len_from_expressions(expressions))

    # Determine output counts
    num_outputs = len(expressions)
    num_ns = st_len  # First st_len expressions are next-state bits
    num_z = num_outputs - st_len  # Remaining are primary outputs

    # Build node name lists
    input_nodes = [f'{input_node_prefix}[{i}]' for i in range(inp_len)]
    state_nodes = [f'{state_node_prefix}[{i}]' for i in range(st_len)]
    next_state_nodes = [f'{next_state_node_prefix}[{i}]' for i in range(st_len)]
    output_nodes = [f'{output_node_prefix}[{i}]' for i in range(num_z)]

    # External input nodes only (state nodes come from DFF outputs)
    all_input_names = input_nodes + [clock_node, reset_node]
    all_output_names = output_nodes + state_nodes

    lines = []
    lines.append('INPUTS ' + ' '.join(all_input_names))
    lines.append('OUTPUTS ' + ' '.join(all_output_names))

    # Node counter for intermediate signals
    node_counter = [0]

    def new_node():
        node_counter[0] += 1
        return f'n{node_counter[0]}'

    # NOT gate cache: variable name -> NOT gate output node
    not_cache = {}

    def get_not_output(var_name):
        """Get or create a NOT gate output for a negated literal."""
        if var_name not in not_cache:
            not_out = new_node()
            lines.append(f'NOT {var_name} {not_out}')
            not_cache[var_name] = not_out
        return not_cache[var_name]

    # Process each expression (NS bits first, then Z bits)
    for expr_idx, expr_str in enumerate(expressions):
        terms = parse_sop_terms(expr_str)

        # Determine output node name
        if expr_idx < num_ns:
            output_node = next_state_nodes[expr_idx]
        else:
            z_idx = expr_idx - num_ns
            output_node = output_nodes[z_idx]

        # Process each term: AND of literals
        term_outputs = []
        for term in terms:
            # Convert literals to node names
            lit_nodes = []
            for var_name, is_negated in term:
                if is_negated:
                    lit_nodes.append(get_not_output(var_name))
                else:
                    lit_nodes.append(var_name)

            # Build AND tree with 2-input AND gates only
            if len(lit_nodes) == 1:
                term_out = lit_nodes[0]
            else:
                current = lit_nodes[0]
                for k in range(1, len(lit_nodes)):
                    out = new_node()
                    lines.append(f'AND {current} {lit_nodes[k]} {out}')
                    current = out
                term_out = current

            term_outputs.append(term_out)

        # Combine term outputs with OR tree (2-input OR gates only)
        if len(term_outputs) == 1:
            term_out = term_outputs[0]
            # Single term: use BUFF to connect to output
            lines.append(f'BUFF {term_out} {output_node}')
        else:
            current = term_outputs[0]
            for k in range(1, len(term_outputs)):
                out = output_node if k == len(term_outputs) - 1 else new_node()
                lines.append(f'OR {current} {term_outputs[k]} {out}')
                current = out

    # Add DFFs for each state bit
    # DFF d clk rst q: D=input, Q=output (present state)
    for i in range(st_len):
        d_input = next_state_nodes[i]
        q_output = state_nodes[i]
        lines.append(f'DFF {d_input} {clock_node} {reset_node} {q_output}')

    netlist_text = '\n'.join(lines) + '\n'

    # Write to file
    with open(netlist_path, 'w', encoding='utf-8') as f:
        f.write(netlist_text)

    return netlist_text


def generate_netlist_from_csv(csv_path, target_cost, netlist_path='fsm_netlist.txt'):
    """Convenience: load CSV, minimize, and generate netlist."""
    stt_df = pd.read_csv(csv_path)
    result = run_minimization(stt_df, target_cost)
    netlist_text = generate_fsm_netlist(result, netlist_path=netlist_path)
    return result, netlist_text


def generate_netlist_from_json(json_path, target_cost, netlist_path='fsm_netlist.txt'):
    """Convenience: load JSON, minimize, and generate netlist."""
    from fsm_parser import json_to_dataframe
    stt_df = json_to_dataframe(json_path)
    result = run_minimization(stt_df, target_cost)
    netlist_text = generate_fsm_netlist(result, netlist_path=netlist_path)
    return result, netlist_text


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python fsm_netlist.py <csv_or_json_file> "
              "[target_cost] [output_netlist]")
        print("\nExamples:")
        print("  python fsm_netlist.py fsm.csv 5 fsm_netlist.txt")
        print("  python fsm_netlist.py examples/fsm.json 5 fsm_netlist.txt")
        sys.exit(1)

    input_path = sys.argv[1]
    target_cost = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    output_netlist = sys.argv[3] if len(sys.argv) > 3 else 'fsm_netlist.txt'

    # Load input
    if input_path.endswith('.json'):
        from fsm_parser import json_to_dataframe
        stt_df = json_to_dataframe(input_path)
    else:
        stt_df = pd.read_csv(input_path)

    # Run minimization
    result = run_minimization(stt_df, target_cost)

    # Generate netlist
    netlist_text = generate_fsm_netlist(result, netlist_path=output_netlist)

    print(f"Netlist saved to {output_netlist}")
    print(f"Max cost (critical path): {result['max_cost']}")
    print(f"States: {len(result['final_states'])} "
          f"(state bits: {math.ceil(math.log2(len(result['final_states'])) or 1)})")
    print("\nNetlist preview:")
    print(netlist_text[:800])
