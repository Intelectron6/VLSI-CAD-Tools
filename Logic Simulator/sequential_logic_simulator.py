import argparse
import csv
import os
import re
from pathlib import Path

import circuit_modules
from matplotlib import pyplot as plt


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
    header_tokens = first_line_tokens if set(first_line_tokens).issubset(set(input_nodes)) else None
    data_lines = lines[1:] if header_tokens is not None else lines

    vectors = []
    for line in data_lines:
        values = split_tokens(line)
        if header_tokens is None:
            if len(values) != len(input_nodes):
                raise ValueError(f'Expected {len(input_nodes)} values per input vector, got {len(values)}')
            mapping = {name: val for name, val in zip(input_nodes, values)}
        else:
            if len(values) != len(header_tokens):
                raise ValueError(f'Expected {len(header_tokens)} values per input vector, got {len(values)}')
            mapping = {name: val for name, val in zip(header_tokens, values)}

        row = []
        for name in input_nodes:
            if name not in mapping:
                raise ValueError(f'Missing input value for {name}')
            row.append(mapping[name])
        vectors.append(tuple(row))

    return vectors


def write_csv_report(report_path, input_nodes, input_vectors, output_nodes, outputs):
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open('w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        header = ['step'] + list(input_nodes) + list(output_nodes)
        writer.writerow(header)
        for step_index, (input_vector, output_vector) in enumerate(zip(input_vectors, outputs)):
            writer.writerow([step_index] + list(input_vector) + list(output_vector))


def seed_flipflop_values(node_vals, ckt_nodes):
    for node in ckt_nodes:
        if node[0] == 'DFF':
            ff_name = node[4]
            if ff_name in circuit_modules._flipflop_state:
                node_vals[ff_name] = circuit_modules._flipflop_state[ff_name]['q']


def get_node_value(node_vals, name):
    return node_vals.get(name, 'x')


def evaluate_cycle(input_nodes, input_vector, ckt_nodes, output_nodes):
    node_vals = {}
    for name, value in zip(input_nodes, input_vector):
        node_vals[name] = value

    seed_flipflop_values(node_vals, ckt_nodes)

    for node in ckt_nodes:
        if node[0] == 'DFF':
            continue
        if node[0] == 'NOT':
            node_vals[node[2]] = circuit_modules.not_gate(get_node_value(node_vals, node[1]))
        elif node[0] == 'BUFF':
            node_vals[node[2]] = circuit_modules.buffer(get_node_value(node_vals, node[1]))
        elif node[0] == 'AND':
            node_vals[node[3]] = circuit_modules.and_gate(get_node_value(node_vals, node[1]), get_node_value(node_vals, node[2]))
        elif node[0] == 'OR':
            node_vals[node[3]] = circuit_modules.or_gate(get_node_value(node_vals, node[1]), get_node_value(node_vals, node[2]))
        elif node[0] == 'NAND':
            node_vals[node[3]] = circuit_modules.nand_gate(get_node_value(node_vals, node[1]), get_node_value(node_vals, node[2]))
        elif node[0] == 'NOR':
            node_vals[node[3]] = circuit_modules.nor_gate(get_node_value(node_vals, node[1]), get_node_value(node_vals, node[2]))
        elif node[0] == 'XOR':
            node_vals[node[3]] = circuit_modules.xor_gate(get_node_value(node_vals, node[1]), get_node_value(node_vals, node[2]))
        elif node[0] == 'XNOR':
            node_vals[node[3]] = circuit_modules.xnor_gate(get_node_value(node_vals, node[1]), get_node_value(node_vals, node[2]))
        elif node[0] == 'MUX2x1':
            node_vals[node[4]] = circuit_modules.mux_2x1(get_node_value(node_vals, node[1]), get_node_value(node_vals, node[2]), get_node_value(node_vals, node[3]))

    for node in ckt_nodes:
        if node[0] == 'DFF':
            node_vals[node[4]] = circuit_modules.d_flipflop(node[4], get_node_value(node_vals, node[1]), get_node_value(node_vals, node[2]), get_node_value(node_vals, node[3]))

    return [node_vals[name] for name in output_nodes]


def simulate_cycles(input_nodes, input_vectors, ckt_nodes, output_nodes):
    if not input_vectors:
        raise ValueError('At least one input vector is required')

    circuit_modules.reset_flipflop_states()
    results = []
    for input_vector in input_vectors:
        results.append(evaluate_cycle(input_nodes, input_vector, ckt_nodes, output_nodes))
    return results


def build_signal_values(input_nodes, input_vectors, output_nodes, outputs):
    signal_values = {}
    for index, name in enumerate(input_nodes):
        signal_values[name] = [vector[index] for vector in input_vectors]
    for index, name in enumerate(output_nodes):
        signal_values[name] = [values[index] for values in outputs]
    return signal_values


def format_cycle_report(step_index, input_nodes, input_vector, output_nodes, output_values):
    input_parts = [f'{name}={value}' for name, value in zip(input_nodes, input_vector)]
    output_parts = [f'{name}={value}' for name, value in zip(output_nodes, output_values)]
    input_text = ' '.join(input_parts)
    output_text = ' '.join(output_parts)
    return f'step {step_index}: {input_text} -> {output_text}'


def plot_waveforms(signal_values, title='Waveform', output_path=None):
    if output_path is None:
        output_path = os.path.join(os.path.dirname(__file__), 'waveform.png')

    signals = list(signal_values.keys())
    series = [signal_values[name] for name in signals]

    fig, axes = plt.subplots(len(signals), 1, figsize=(10, 2 * len(signals)), sharex=True)
    if len(signals) == 1:
        axes = [axes]

    for ax, name, values in zip(axes, signals, series):
        numeric_values = []
        for value in values:
            if value in ['1', 1, True]:
                numeric_values.append(1)
            elif value in ['0', 0, False]:
                numeric_values.append(0)
            else:
                numeric_values.append(0.5)

        for i in range(len(values) - 1):
            color = 'red' if values[i] not in ['0', 0, False, '1', 1, True] else 'C0'
            linestyle = ':' if color == 'red' else '-'
            linewidth = 2.5 if color == 'red' else 1.8

            ax.plot(
                [i, i + 1],
                [numeric_values[i], numeric_values[i]],
                color=color,
                linestyle=linestyle,
                linewidth=linewidth
            )
            ax.plot(
                [i + 1, i + 1],
                [numeric_values[i], numeric_values[i + 1]],
                color='C0',
                linewidth=1.8
            )

        final_color = 'red' if values[-1] not in ['0', 0, False, '1', 1, True] else 'C0'
        ax.scatter(
            len(values) - 1,
            numeric_values[-1],
            color=final_color,
            s=40,
            zorder=5
        )

        ax.set_ylabel(name)
        ax.set_ylim(-0.1, 1.1)
        ax.set_yticks([0, 0.5, 1])
        ax.set_yticklabels(['0', 'X', '1'])
        ax.set_xlim(0, len(values) - 1)
        ax.grid(True, alpha=0.3)

    axes[-1].set_xlabel('Cycle')
    fig.suptitle(title)
    plt.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    print(f'Waveform saved to {output_path}')


def parse_args():
    parser = argparse.ArgumentParser(description='Simulate a generic digital logic circuit from a netlist and stimulus file.')
    parser.add_argument('--netlist', required=True, help='Path to the netlist file')
    parser.add_argument('--stimulus', required=True, help='Path to the stimulus file')
    parser.add_argument('--output-dir', default=None, help='Directory for generated report and waveform files')
    parser.add_argument('--report', default=None, help='Path to the output report file')
    parser.add_argument('--waveform', default=None, help='Path to the waveform image file')
    parser.add_argument('--title', default=None, help='Title for the waveform plot')
    return parser.parse_args()


def resolve_path(path_value, base_dir, default_name=None):
    path = Path(path_value)
    if not path.is_absolute():
        path = base_dir / path
    path = path.resolve()
    if default_name is not None and path.suffix == '':
        path = path.with_suffix(default_name)
    return path


def resolve_output_path(path_value, base_dir, output_dir, default_name):
    if path_value is None:
        return (output_dir / default_name).resolve()

    path = Path(path_value)
    if path.is_absolute():
        return path.resolve()
    if path.parent != Path('.'):
        return (base_dir / path).resolve()
    return (output_dir / path).resolve()


def main():
    args = parse_args()
    base_dir = Path(__file__).resolve().parent

    netlist_path = resolve_path(args.netlist, base_dir)
    stimulus_path = resolve_path(args.stimulus, base_dir)
    output_dir = resolve_path(args.output_dir or 'Work', base_dir) if args.output_dir else (base_dir / 'Work').resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    report_path = resolve_output_path(args.report, base_dir, output_dir, f'{netlist_path.stem}_outputs.csv')
    waveform_path = resolve_output_path(args.waveform, base_dir, output_dir, f'{netlist_path.stem}_waveform.png')

    input_nodes, output_nodes, ckt_nodes = load_netlist(netlist_path)
    input_vectors = load_input_vectors(stimulus_path, input_nodes)

    outputs = simulate_cycles(input_nodes, input_vectors, ckt_nodes, output_nodes)
    print('Step-based simulation results:')

    for i, out in enumerate(outputs):
        print(format_cycle_report(i, input_nodes, input_vectors[i], output_nodes, out))

    write_csv_report(report_path, input_nodes, input_vectors, output_nodes, outputs)

    signal_values = build_signal_values(input_nodes, input_vectors, output_nodes, outputs)
    plot_waveforms(signal_values, title=args.title or f'{netlist_path.stem} waveform', output_path=waveform_path)
    print(f'Outputs saved to {report_path}')


if __name__ == '__main__':
    main()