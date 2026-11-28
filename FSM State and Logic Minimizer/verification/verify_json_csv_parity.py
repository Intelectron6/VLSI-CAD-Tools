"""
Verify that CSV and JSON input paths produce identical minimization results.

Runs fsm_minimizer.run_minimization() on:
1. examples/fsm.csv (CSV path)
2. examples/fsm.json converted via fsm_parser.json_to_dataframe() (JSON path)

Compares the expressions and costs from both paths.
"""

import sys
import os

# Add the FSM directory (parent of verification/) to path
FSM_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, FSM_DIR)

import pandas as pd
from fsm_minimizer import run_minimization
from fsm_parser import json_to_dataframe


def run_csv_path(csv_path, target_cost):
    """Run minimization from a CSV file."""
    stt_df = pd.read_csv(os.path.join(FSM_DIR, csv_path))
    return run_minimization(stt_df, target_cost)


def run_json_path(json_path, target_cost):
    """Run minimization from a JSON file via the parser."""
    stt_df = json_to_dataframe(os.path.join(FSM_DIR, json_path))
    return run_minimization(stt_df, target_cost)


def compare_results(csv_result, json_result, label):
    """Compare two result dicts and report differences."""
    print(f"\n{'='*60}")
    print(f"COMPARISON: {label}")
    print(f"{'='*60}")

    all_match = True

    # Compare final states
    csv_states = csv_result['final_states']
    json_states = json_result['final_states']
    if csv_states == json_states:
        print(f"Final states: MATCH ({csv_states})")
    else:
        print(f"Final states: MISMATCH")
        print(f"  CSV:    {csv_states}")
        print(f"  JSON:   {json_states}")
        all_match = False

    # Compare expressions
    csv_exprs = csv_result['expressions']
    json_exprs = json_result['expressions']
    if len(csv_exprs) != len(json_exprs):
        print(f"Expression count: MISMATCH (CSV={len(csv_exprs)}, JSON={len(json_exprs)})")
        all_match = False
    else:
        for i, (ce, je) in enumerate(zip(csv_exprs, json_exprs)):
            if ce == je:
                print(f"Expression {i}: MATCH ({ce})")
            else:
                print(f"Expression {i}: MISMATCH")
                print(f"  CSV:    {ce}")
                print(f"  JSON:   {je}")
                all_match = False

    # Compare costs
    csv_costs = csv_result['costs']
    json_costs = json_result['costs']
    if csv_costs == json_costs:
        print(f"Costs: MATCH ({csv_costs})")
    else:
        print(f"Costs: MISMATCH")
        print(f"  CSV:    {csv_costs}")
        print(f"  JSON:   {json_costs}")
        all_match = False

    # Compare max cost
    if csv_result['max_cost'] == json_result['max_cost']:
        print(f"Max cost: MATCH ({csv_result['max_cost']})")
    else:
        print(f"Max cost: MISMATCH (CSV={csv_result['max_cost']}, JSON={json_result['max_cost']})")
        all_match = False

    print(f"\nResult: {'ALL MATCH' if all_match else 'MISMATCH FOUND'}")
    return all_match


def main():
    target_cost = 6

    all_pass = True

    # Test fsm / fsm.csv
    print("\n" + "="*60)
    print("TEST 1: fsm.csv vs examples/fsm.json")
    print("="*60)
    csv_result = run_csv_path('examples/fsm.csv', target_cost)
    json_result = run_json_path('examples/fsm.json', target_cost)
    if not compare_results(csv_result, json_result, 'fsm.csv vs fsm.json'):
        all_pass = False

    # Test fsm2 / fsm2.csv
    print("\n" + "="*60)
    print("TEST 2: fsm2.csv vs examples/fsm2.json")
    print("="*60)
    csv_result = run_csv_path('examples/fsm2.csv', target_cost)
    json_result = run_json_path('examples/fsm2.json', target_cost)
    if not compare_results(csv_result, json_result, 'fsm2.csv vs fsm2.json'):
        all_pass = False

    print("\n" + "="*60)
    if all_pass:
        print("ALL PARITY TESTS PASSED")
    else:
        print("SOME PARITY TESTS FAILED")
    print("="*60)

    return 0 if all_pass else 1


if __name__ == '__main__':
    sys.exit(main())
