"""
Phase 3 sanity check pipeline:
  1. Generate a netlist from espresso.py (minimized SOP)
  2. Create a stimulus CSV covering all input combinations
  3. Run the Logic Simulator on the generated netlist
  4. Compare simulator outputs against expected truth table

Usage:
    python verify_phase3.py
"""

import csv
import itertools
import os
import subprocess
import sys
import tempfile

PYTHON = "F:\\Anaconda_Python\\python.exe"
ESPRESSO = "espresso.py"
WORKDIR = os.path.dirname(os.path.abspath(__file__))

LOGIC_SIM_DIR = os.path.join(WORKDIR, "..", "Logic Simulator")
RUN_SIM = os.path.join(LOGIC_SIM_DIR, "run_sim.py")


def expected_f(assignment):
    """Expected f for logic.csv function: f = x[1] OR (x[0] AND x[2])"""
    x0 = assignment[0]
    x1 = assignment[1]
    x2 = assignment[2]
    return int(x1 or (x0 and x2))


def run_espresso(input_csv, tau, netlist_path):
    """Run espresso.py and return (expression, cost)."""
    cmd = [
        PYTHON, ESPRESSO,
        '--input', input_csv,
        '--tau', str(tau),
        '--netlist', netlist_path,
    ]
    result = subprocess.run(
        cmd,
        input='\n',
        capture_output=True,
        text=True,
        cwd=WORKDIR,
    )
    if result.returncode != 0:
        print(f"  espresso.py ERROR: {result.stderr}")
        return None, None
    expr = None
    cost = None
    for line in result.stdout.splitlines():
        if line.startswith('f ='):
            expr = line[len('f ='):].strip()
        elif line.startswith('Final cost:'):
            cost = int(line.split(':')[1].strip())
    return expr, cost


def generate_stimulus(width, stimulus_path):
    """Generate a stimulus CSV with all 2^width input combinations.

    Uses node names x[0], x[1], ... matching the netlist input names.
    """
    with open(stimulus_path, 'w', newline='') as f:
        writer = csv.writer(f)
        # Header row matching input node names (so Logic Simulator treats it as header)
        header = [f'x[{i}]' for i in range(width)]
        writer.writerow(header)
        for bits in itertools.product([0, 1], repeat=width):
            writer.writerow(list(bits))


def run_logic_simulator(netlist_path, stimulus_path, report_path):
    """Run the Logic Simulator (combinational) and return output rows."""
    cmd = [
        PYTHON, os.path.join(LOGIC_SIM_DIR, 'combinational_logic_simulator.py'),
        '--netlist', netlist_path,
        '--stimulus', stimulus_path,
        '--output', report_path,
    ]
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=LOGIC_SIM_DIR,
    )
    if result.returncode != 0:
        print(f"  Logic Simulator ERROR: {result.stderr}")
        return None
    # Read the report CSV
    rows = []
    with open(report_path, newline='') as f:
        reader = csv.reader(f)
        header = next(reader)
        for row in reader:
            rows.append(row)
    return header, rows


def main():
    all_pass = True

    with tempfile.TemporaryDirectory() as tmpdir:
        netlist_path = os.path.join(tmpdir, 'ckt.txt')
        stimulus_path = os.path.join(tmpdir, 'stimulus.csv')
        report_path = os.path.join(tmpdir, 'report.csv')

        # --- Step 1: Generate netlist from espresso ---
        print("=" * 60)
        print("STEP 1: Generate netlist from espresso.py")
        print("=" * 60)
        expr, cost = run_espresso('logic.csv', 5, netlist_path)
        if expr is None:
            print("  FAILED: espresso.py did not produce output")
            return 1
        print(f"  Expression: f = {expr}")
        print(f"  Cost: {cost}")

        # Read and display the netlist
        with open(netlist_path) as f:
            netlist = f.read()
        print(f"  Netlist:\n{netlist}")

        # --- Step 2: Generate stimulus ---
        print("=" * 60)
        print("STEP 2: Generate stimulus (all 2^3 input combinations)")
        print("=" * 60)
        width = 3
        generate_stimulus(width, stimulus_path)
        print(f"  Stimulus written to {stimulus_path}")
        with open(stimulus_path) as f:
            print(f.read())

        # --- Step 3: Run Logic Simulator ---
        print("=" * 60)
        print("STEP 3: Run Logic Simulator on generated netlist")
        print("=" * 60)
        result = run_logic_simulator(netlist_path, stimulus_path, report_path)
        if result is None:
            print("  FAILED: Logic Simulator did not produce output")
            return 1
        header, rows = result
        print(f"  Report header: {header}")
        print(f"  Rows: {len(rows)}")

        # --- Step 4: Verify against expected truth table ---
        print("=" * 60)
        print("STEP 4: Verify against expected truth table")
        print("=" * 60)

        # Find the output column index
        output_col = None
        for i, col in enumerate(header):
            if col == 'f':
                output_col = i
                break
        if output_col is None:
            print("  FAILED: No 'f' column in report")
            return 1

        # Input columns are x[0], x[1], x[2] but in the netlist they're
        # ordered x[0] x[1] x[2]. The header order depends on input_nodes order.
        input_cols = []
        for i, col in enumerate(header):
            if col.startswith('x['):
                input_cols.append((i, col))
        input_cols.sort(key=lambda t: int(t[1][2:-1]))  # sort by index

        print(f"  Input columns: {input_cols}")
        print(f"  Output column: {output_col} ('f')")

        for row_idx, row in enumerate(rows):
            # Extract input values
            assignment = []
            for col_idx, col_name in input_cols:
                assignment.append(int(row[col_idx]))
            sim_output = int(row[output_col])
            expected = expected_f(assignment)

            status = "PASS" if sim_output == expected else "FAIL"
            if sim_output != expected:
                all_pass = False
            print(
                f"  Row {row_idx}: x[{assignment[0]}] x[{assignment[1]}] x[{assignment[2]}] "
                f"-> sim={sim_output} expected={expected} [{status}]"
            )

    print("=" * 60)
    if all_pass:
        print("SANITY CHECK: ALL TESTS PASSED")
    else:
        print("SANITY CHECK: SOME TESTS FAILED")
    print("=" * 60)
    return 0 if all_pass else 1


if __name__ == '__main__':
    sys.exit(main())