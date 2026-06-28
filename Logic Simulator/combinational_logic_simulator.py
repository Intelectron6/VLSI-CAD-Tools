import argparse
import csv
import os
import re
from pathlib import Path

import circuit_modules


def split_tokens(line):
    return [token.strip() for token in re.split(r'[\s,]+', line.strip()) if token.strip()]


def load_netlist(netlist_path):
    with open(netlist_path, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]

    if len(lines) < 2:
        raise ValueError('Netlist must contain at least input and output lines')

    input_nodes = lines[0].split()[1:]
    output_nodes = lines[1].split()[1:]
    ckt_nodes = [line.split() for line in lines[2:]]
    return input_nodes, output_nodes, ckt_nodes


def load_input_vectors(stimulus_path, input_nodes):
    with open(stimulus_path, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip() and not line.lstrip().startswith('#')]

    if not lines:
        raise ValueError('Stimulus file is empty')

    first_line_tokens = split_tokens(lines[0])
    data_lines = lines[1:] if len(first_line_tokens) == len(input_nodes) and set(first_line_tokens) == set(input_nodes) else lines

    vectors = []
    for line in data_lines:
        values = split_tokens(line)
        if len(values) == 1 and len(values[0]) == len(input_nodes):
            values = list(values[0])
        if len(values) != len(input_nodes):
            raise ValueError(f'Expected {len(input_nodes)} values per input vector, got {len(values)}')
        vectors.append(tuple(values))

    return vectors


def write_csv_report(report_path, input_nodes, input_vectors, output_nodes, outputs):
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open('w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        header = ['step'] + list(input_nodes) + list(output_nodes)
        writer.writerow(header)
        for step_index, (input_vector, output_vector) in enumerate(zip(input_vectors, outputs)):
            writer.writerow([step_index] + list(input_vector) + list(output_vector))


def format_vector(input_nodes, input_vector, output_nodes, output_vector):
    input_text = ' '.join(f'{name}={value}' for name, value in zip(input_nodes, input_vector))
    output_text = ' '.join(f'{name}={value}' for name, value in zip(output_nodes, output_vector))
    return f'{input_text} -> {output_text}'


def parse_args():
    parser = argparse.ArgumentParser(description='Simulate a combinational digital logic circuit from a netlist and stimulus file.')
    parser.add_argument('--netlist', required=True, help='Path to the netlist file')
    parser.add_argument('--stimulus', required=True, help='Path to the stimulus file')
    parser.add_argument('--output', default=None, help='Path to the output report file')
    return parser.parse_args()


def resolve_path(path_value, base_dir):
    path = Path(path_value)
    if not path.is_absolute():
        path = base_dir / path
    return path.resolve()


def main():
    args = parse_args()
    base_dir = Path(__file__).resolve().parent

    netlist_path = resolve_path(args.netlist, base_dir)
    stimulus_path = resolve_path(args.stimulus, base_dir)
    report_path = resolve_path(args.output, base_dir)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    input_nodes, output_nodes, ckt_nodes = load_netlist(netlist_path)
    input_vectors = load_input_vectors(stimulus_path, input_nodes)

    outputs = []
    for input_vector in input_vectors:
        output_vector = circuit_modules.ckt(input_nodes, input_vector, ckt_nodes, output_nodes)
        outputs.append(tuple(output_vector))

    write_csv_report(report_path, input_nodes, input_vectors, output_nodes, outputs)
    print(f'Outputs saved to {report_path}')


if __name__ == '__main__':
    main()

