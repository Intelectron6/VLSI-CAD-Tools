"""
Extended Phase 3 sanity check: tests multiple expressions including ones
that require NOT gates, AND cascading (>2 literals), and OR cascading (>2 terms).

Reads input node names directly from the generated netlist so the stimulus
matches exactly what the Logic Simulator expects.
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
WORKDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGIC_SIM_DIR = os.path.join(WORKDIR, "..", "Logic Simulator")


def parse_netlist_inputs(netlist_path):
    """Read the 'input' line from a netlist to get input node names."""
    with open(netlist_path) as f:
        first_line = f.readline().strip()
    # Format: 'input x[0] x[1] x[2]'
    tokens = first_line.split()
    if tokens and tokens[0] == 'input':
        return tokens[1:]
    return []


def run_espresso(input_csv, tau, netlist_path):
    cmd = [PYTHON, ESPRESSO, '--input', input_csv, '--tau', str(tau), '--netlist', netlist_path]
    result = subprocess.run(cmd, input='\n', capture_output=True, text=True, cwd=WORKDIR)
    if result.returncode != 0:
        print(f"  espresso.py ERROR: {result.stderr}")
        return None, None
    expr, cost = None, None
    for line in result.stdout.splitlines():
        if line.startswith('f ='):
            expr = line[len('f ='):].strip()
        elif line.startswith('Final cost:'):
            cost = int(line.split(':')[1].strip())
    return expr, cost


def generate_stimulus(input_names, stimulus_path):
    """Generate a stimulus CSV with all 2^width input combinations."""
    width = len(input_names)
    with open(stimulus_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(input_names)
        for bits in itertools.product([0, 1], repeat=width):
            writer.writerow(list(bits))


def run_logic_simulator(netlist_path, stimulus_path, report_path):
    cmd = [PYTHON, os.path.join(LOGIC_SIM_DIR, 'combinational_logic_simulator.py'),
           '--netlist', netlist_path, '--stimulus', stimulus_path, '--output', report_path]
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=LOGIC_SIM_DIR)
    if result.returncode != 0:
        print(f"  Logic Simulator ERROR: {result.stderr}")
        return None
    rows = []
    with open(report_path, newline='') as f:
        reader = csv.reader(f)
        header = next(reader)
        for row in reader:
            rows.append(row)
    return header, rows


def load_truth_table(csv_path, width):
    """Load a truth-table CSV, returning dict mapping netlist input tuple -> output.

    CSV columns are x{width-1}, ..., x0 (e.g. x4,x3,x2,x1,x0 for width=5).
    Netlist x[N] corresponds to CSV column x{width-1-N}, so netlist input order
    (x[0], x[1], ...) matches CSV header order (x{width-1}, ..., x0).

    Output of 'x' (don't-care) is stored as None.
    """
    lookup = {}
    with open(csv_path, newline='') as f:
        reader = csv.reader(f)
        header = next(reader)
        f_idx = header.index('f')
        # CSV header order: x{width-1}, ..., x0 -> matches netlist x[0], x[1], ...
        x_col_indices = [i for i, c in enumerate(header) if c.startswith('x')]
        # They should already be in header order; just verify count
        assert len(x_col_indices) == width, f"Expected {width} x columns, got {len(x_col_indices)}"
        for row in reader:
            inputs = tuple(int(row[i]) for i in x_col_indices)
            out_val = row[f_idx]
            output = None if out_val == 'x' else int(out_val)
            lookup[inputs] = output
    return lookup


def test_case(csv_file, tau, csv_path_for_expected, width, description):
    """Test one CSV file through the full pipeline."""
    print(f"\n{'='*60}")
    print(f"TEST: {description}")
    print(f"{'='*60}")

    with tempfile.TemporaryDirectory() as tmpdir:
        netlist_path = os.path.join(tmpdir, 'ckt.txt')
        stimulus_path = os.path.join(tmpdir, 'stimulus.csv')
        report_path = os.path.join(tmpdir, 'report.csv')

        # Step 1: Generate netlist
        expr, cost = run_espresso(csv_file, tau, netlist_path)
        if expr is None:
            print("  FAILED: espresso.py error")
            return False
        print(f"  Expression: f = {expr}")
        print(f"  Cost: {cost}")
        with open(netlist_path) as f:
            print(f"  Netlist:\n{f.read()}")

        # Step 2: Read input names from netlist
        input_names = parse_netlist_inputs(netlist_path)
        print(f"  Netlist inputs: {input_names}")

        # Step 3: Generate stimulus matching netlist input names
        generate_stimulus(input_names, stimulus_path)

        # Step 4: Run Logic Simulator
        result = run_logic_simulator(netlist_path, stimulus_path, report_path)
        if result is None:
            print("  FAILED: Logic Simulator error")
            return False
        header, rows = result

        # Step 5: Load expected truth table from CSV
        # Netlist x[N] = CSV column header[N] = x{width-1-N}
        # load_truth_table returns keys in CSV header order (x{width-1}, ..., x0)
        # which matches netlist order (x[0], x[1], ...) directly.
        lookup = load_truth_table(os.path.join(WORKDIR, csv_path_for_expected), width)

        # Step 6: Verify
        # Extract variable numbers from netlist input names (e.g. 'x[3]' -> 3)
        netlist_var_nums = []
        for col in input_names:
            m = re.match(r'x\[(\d+)\]', col)
            netlist_var_nums.append(int(m.group(1)) if m else -1)

        input_cols = []
        for i, col in enumerate(header):
            if col.startswith('x['):
                input_cols.append((i, col))
        input_cols.sort(key=lambda t: int(t[1][2:-1]))

        output_col = None
        for i, col in enumerate(header):
            if col == 'f':
                output_col = i
                break

        all_pass = True
        dc_skipped = 0
        for row_idx, row in enumerate(rows):
            # Netlist input values, mapped by variable number
            netlist_vals_by_var = {}
            for col_idx, col_name in input_cols:
                m = re.match(r'x\[(\d+)\]', col_name)
                var_num = int(m.group(1))
                netlist_vals_by_var[var_num] = int(row[col_idx])

            # Build full CSV-width input tuple for lookup
            # Unused variables default to 0
            csv_vals = [0] * width
            for var_num in range(width):
                if var_num in netlist_vals_by_var:
                    csv_vals[var_num] = netlist_vals_by_var[var_num]
            csv_key = tuple(csv_vals)

            sim_output = int(row[output_col])
            expected = lookup.get(csv_key)

            if expected is None:
                # Don't-care: any output is acceptable
                dc_skipped += 1
                print(f"  Row {row_idx}: sim={sim_output} expected=DC [SKIP]")
                continue

            if sim_output != expected:
                all_pass = False
                print(f"  Row {row_idx}: sim={sim_output} expected={expected} [FAIL]")
            else:
                print(f"  Row {row_idx}: sim={sim_output} expected={expected} [PASS]")

        if dc_skipped > 0:
            print(f"  ({dc_skipped} don't-care rows skipped)")

        return all_pass


def main():
    all_pass = True

    # Test 1: logic.csv (3 variables)
    r1 = test_case('examples/logic.csv', 5, 'examples/logic.csv', 3, 'logic.csv tau=5')
    all_pass = all_pass and r1

    # Test 2: logic2.csv (4 variables, majority-like function)
    r2 = test_case('examples/logic2.csv', 6, 'examples/logic2.csv', 4, 'logic2.csv tau=6')
    all_pass = all_pass and r2

    # Test 3: logic3.csv (5 variables, complex function with don't-cares)
    r3 = test_case('examples/logic3.csv', 8, 'examples/logic3.csv', 5, 'logic3.csv tau=8')
    all_pass = all_pass and r3

    print(f"\n{'='*60}")
    if all_pass:
        print("EXTENDED SANITY CHECK: ALL TESTS PASSED")
    else:
        print("EXTENDED SANITY CHECK: SOME TESTS FAILED")
    print(f"{'='*60}")
    return 0 if all_pass else 1


if __name__ == '__main__':
    sys.exit(main())