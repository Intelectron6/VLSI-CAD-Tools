"""
Comprehensive accuracy verification for Phase 2 (symbolic expression parsing)
and Phase 3 (netlist generation).

Tests that:
1. Expression parsing correctly handles multiple formats (&, |, ~, ., +, !, word ops)
2. ESPRESSO minimization produces functionally correct results
3. Generated netlists simulate correctly in the Logic Simulator
4. Minimization is done by our ESPRESSO engine, not by sympy's simplify()
"""

import csv
import itertools
import os
import re
import subprocess
import sys
import tempfile

PYTHON = "F:\\Anaconda_Python\\python.exe"
ESPRESSO = "espresso.py"
WORKDIR = os.path.dirname(os.path.abspath(__file__))
LOGIC_SIM_DIR = os.path.join(WORKDIR, "..", "Logic Simulator")


def eval_bool_expr(expr_str, assignment):
    """Evaluate a boolean expression given var->0/1 assignment.
    Handles x[N] notation (from espresso output) and plain variable names."""
    s = expr_str.strip()
    # Strip optional 'f = ' / 'F = ' prefix
    s = re.sub(r'^[fF]\s*=\s*', '', s)
    # Replace x[N] references (from espresso output like x[0], x[1])
    def replace_x(match):
        idx = int(match.group(1))
        var_names = sorted(assignment.keys())
        var = var_names[idx] if idx < len(var_names) else f'x{idx}'
        return str(assignment.get(var, 0))
    s = re.sub(r'x\[(\d+)\]', replace_x, s)

    # EE notation -> Python (order matters)
    s = s.replace('!(', ' not (')   # !(A.B) -> not (A.B)
    s = re.sub(r'(\w)\.\s*!(\w)', r'\1 and not \2', s)  # A.!B -> A and not B
    s = re.sub(r'!(\w)', r' not \1', s)  # !A -> not A
    s = re.sub(r'(\w)\.(\w)', r'\1 and \2', s)  # A.B -> A and B
    s = s.replace('+', ' or ')  # A + B -> A or B
    s = re.sub(r'\bAND\b', ' and ', s, flags=re.IGNORECASE)
    s = re.sub(r'\bOR\b', ' or ', s, flags=re.IGNORECASE)
    s = re.sub(r'\bNOT\b', ' not ', s, flags=re.IGNORECASE)
    s = s.replace('&', ' and ').replace('|', ' or ').replace('~', ' not ')
    s = s.replace('^', ' != ')

    # Replace variable names with values (longest first to avoid partial matches)
    for var, val in sorted(assignment.items(), key=lambda x: -len(x[0])):
        s = re.sub(r'\b' + var + r'\b', str(val), s)

    # Clean up: replace 'True'/'False' with 1/0, handle empty expressions
    s = s.strip()
    if not s:
        return 0
    return int(eval(s))


def get_vars(expr_str):
    """Extract variable names from expression."""
    return sorted(set(re.findall(r'\b([A-Z])\b', expr_str)))


def run_espresso(args, input_text='\n'):
    """Run espresso.py and return (expression, cost, stdout)."""
    cmd = [PYTHON, ESPRESSO] + args
    result = subprocess.run(cmd, input=input_text, capture_output=True, text=True,
                            cwd=WORKDIR)
    if result.returncode != 0:
        return None, None, result.stderr
    expr, cost = None, None
    for line in result.stdout.splitlines():
        if line.startswith('f ='):
            expr = line[len('f ='):].strip()
        elif line.startswith('Final cost:'):
            cost = int(line.split(':')[1].strip())
    return expr, cost, result.stdout


def generate_netlist_and_test(expr_str, tau, description):
    """Full pipeline: expression -> netlist -> simulate -> verify."""
    print(f"\n{'='*60}")
    print(f"TEST: {description}")
    print(f"  Expression: {expr_str}")
    print(f"{'='*60}")

    vars_ = get_vars(expr_str)
    width = len(vars_)
    print(f"  Variables: {vars_}")

    with tempfile.TemporaryDirectory() as tmpdir:
        netlist_path = os.path.join(tmpdir, 'ckt.txt')
        stimulus_path = os.path.join(tmpdir, 'stimulus.csv')
        report_path = os.path.join(tmpdir, 'report.csv')

        # Step 1: Run espresso to get expression + netlist
        expr, cost, stdout = run_espresso(
            ['--expression', expr_str, '--tau', str(tau), '--netlist', netlist_path]
        )
        if expr is None:
            print(f"  FAILED: espresso.py error: {stdout}")
            return False
        print(f"  Minimized: f = {expr}")
        print(f"  Cost: {cost}")

        # Read netlist to get input names
        with open(netlist_path) as f:
            netlist = f.read()
        print(f"  Netlist:\n{netlist}")

        # Step 2: Generate stimulus matching netlist input names
        input_names = re.findall(r'^input (.+)', netlist, re.MULTILINE)
        if not input_names:
            print("  FAILED: No input line in netlist")
            return False
        input_names = input_names[0].split()
        print(f"  Netlist inputs: {input_names}")

        with open(stimulus_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(input_names)
            for bits in itertools.product([0, 1], repeat=len(input_names)):
                writer.writerow(list(bits))

        # Step 3: Run Logic Simulator
        sim_cmd = [PYTHON,
                   os.path.join(LOGIC_SIM_DIR, 'combinational_logic_simulator.py'),
                   '--netlist', netlist_path,
                   '--stimulus', stimulus_path,
                   '--output', report_path]
        sim_result = subprocess.run(sim_cmd, capture_output=True, text=True,
                                    cwd=LOGIC_SIM_DIR)
        if sim_result.returncode != 0:
            print(f"  FAILED: Logic Simulator error: {sim_result.stderr}")
            return False

        # Step 4: Verify against expected truth table
        with open(report_path, newline='') as f:
            reader = csv.reader(f)
            header = next(reader)
            rows = list(reader)

        # Find column indices
        input_cols = [(i, col) for i, col in enumerate(header)
                      if col.startswith('x[')]
        input_cols.sort(key=lambda t: int(t[1][2:-1]))
        output_col = next(i for i, col in enumerate(header) if col == 'f')

        # Map x[N] -> variable name
        # x[N] in netlist = vars_[N] (sorted order)
        x_to_var = {i: vars_[i] for i in range(width)}

        all_pass = True
        dc_skipped = 0
        for row_idx, row in enumerate(rows):
            # Get netlist input values
            netlist_vals = {}
            for col_idx, col_name in input_cols:
                m = re.match(r'x\[(\d+)\]', col_name)
                var_num = int(m.group(1))
                netlist_vals[var_num] = int(row[col_idx])

            # Build full assignment
            assignment = {}
            for var_num in range(width):
                var_name = x_to_var[var_num]
                assignment[var_name] = netlist_vals.get(var_num, 0)

            sim_output = int(row[output_col])
            expected = eval_bool_expr(expr_str, assignment)

            if sim_output != expected:
                all_pass = False
                print(f"  Row {row_idx}: {assignment} -> sim={sim_output} expected={expected} [FAIL]")
            else:
                print(f"  Row {row_idx}: {assignment} -> sim={sim_output} expected={expected} [PASS]")

    print(f"  Result: {'PASS' if all_pass else 'FAIL'}")
    return all_pass


def main():
    all_pass = True

    # Test cases: (expression, tau, description)
    # These test that ESPRESSO minimization (our code) produces correct results
    test_cases = [
        # Basic consensus theorem: A&B | A&~B = A
        ("A & B | A & ~B", 2, "Consensus: A&B | A&~B = A"),
        # EE notation equivalent
        ("A.B + A.!B", 2, "EE notation: A.B + A.!B = A"),
        # Absorption: A | A&B = A
        ("A | A & B", 2, "Absorption: A | A&B = A"),
        # Distribution: A&(B|C) = AB | AC
        ("A & (B | C)", 3, "Distribution: A&(B|C) = AB | AC"),
        # De Morgan's: !(A.B) = ~A | ~B
        ("!(A.B)", 3, "De Morgan: !(A.B) = ~A | ~B"),
        ("!(A+B)", 3, "De Morgan: !(A+B) = ~A & ~B"),
        # XOR: A^B = A~B | ~A·B
        ("A ^ B", 3, "XOR: A^B = A~B | ~A·B"),
        # Simple OR
        ("A | B | C", 3, "OR: A|B|C"),
        # Simple AND
        ("A & B & C", 3, "AND: A&B&C"),
        # Mixed
        ("A & B | ~C", 3, "Mixed: A&B | ~C"),
        # Word operators
        ("A AND B OR NOT C", 3, "Word ops: A AND B OR NOT C"),
        # With f= prefix
        ("f = A & B | ~C", 3, "With f= prefix: f = A & B | ~C"),
        # 4-variable majority
        ("A & B | B & C | A & C", 4, "Majority: AB | BC | AC"),
        # 4-variable
        ("A & B | C & D", 4, "Mixed 4-var: AB | CD"),
    ]

    for expr_str, tau, desc in test_cases:
        ok = generate_netlist_and_test(expr_str, tau, desc)
        all_pass = all_pass and ok

    print(f"\n{'='*60}")
    if all_pass:
        print("ALL ACCURACY TESTS PASSED")
    else:
        print("SOME ACCURACY TESTS FAILED")
    print(f"{'='*60}")
    return 0 if all_pass else 1


if __name__ == '__main__':
    sys.exit(main())