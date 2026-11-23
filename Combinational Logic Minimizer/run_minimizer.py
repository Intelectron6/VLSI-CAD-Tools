"""
Interactive TUI for the Combinational Logic Minimizer.

Uses prompt_toolkit for interactive menus and rich for colored output.
Mirrors the user-friendly patterns from Logic Simulator's run_sim.py.

Usage:
    python run_minimizer.py          (interactive TUI)
    python espresso.py --help        (CLI options)
"""

import sys
import csv
import itertools
import subprocess
import tempfile
from pathlib import Path

from prompt_toolkit import prompt
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

import espresso

console = Console()


def get_input(prompt_text):
    """Read user input using prompt_toolkit in TTY mode, input() otherwise."""
    if sys.stdin.isatty():
        return prompt(prompt_text)
    else:
        return input(prompt_text)


def get_selection(title, items):
    """Display a numbered selection menu using prompt_toolkit, with input() fallback."""
    if not items:
        return None
    console.print(f"\n[bold blue]{title}:[/bold blue]")
    for i, item in enumerate(items):
        display_name = item.name if hasattr(item, 'name') else str(item)
        console.print(f"  {i}: {display_name}")

    choice = get_input("Enter the number: ")
    try:
        return items[int(choice)]
    except (ValueError, IndexError):
        console.print("[red]Invalid choice[/red]")
        return None


def show_expression_help():
    """Display accepted expression formats cheat sheet."""
    help_text = (
        "[bold]Accepted expression formats:[/bold]\n"
        "  Symbolic:   A & B | ~C\n"
        "  Word ops:   A AND B OR NOT C\n"
        "  EE notation: A.B + A.!B   ( .=AND, +=OR, !=NOT )\n"
        "  With prefix: f = A & B | ~C\n"
        "  Variables:  single letters A-Z\n"
        "  Examples:   A & B | ~A & C | B & C\n"
        "              !(A.B)           (De Morgan)\n"
        "              A ^ B            (XOR)"
    )
    console.print(Panel(help_text, title="Expression Syntax Help", border_style="blue"))


BUILTIN_EXAMPLES = [
    ("logic.csv", "3-input function with don't-care"),
    ("logic2.csv", "4-input majority-like function"),
    ("logic3.csv", "5-input complex function"),
    ("A & B | ~A & C | B & C", "Consensus theorem example"),
    ("A.B + A.!B", "EE notation: A.B + A.!B = A"),
    ("!(A.B)", "De Morgan: !(A.B) = ~A | ~B"),
    ("A ^ B", "XOR: A ^ B"),
]


def run_interactive_minimizer():
    console.print(Panel.fit(
        "[bold cyan]ESPRESSO Combinational Logic Minimizer - Interactive TUI[/bold cyan]",
        border_style="cyan"
    ))

    # --- Step 1: Select Input Type ---
    console.print("\n[bold blue]Select Input Type:[/bold blue]")
    console.print("  0: Boolean Expression (symbolic)")
    console.print("  1: Truth Table CSV File")
    console.print("  2: Built-in Example")
    console.print("  3: Exit")
    input_choice = get_input("Enter the number: ").strip()

    onset = None
    width = 0
    input_desc = ""

    if input_choice == '0':
        # Boolean expression input
        show_expression_help()
        expr_str = get_input("Enter boolean expression: ").strip()
        if not expr_str:
            console.print("[red]No expression entered[/red]")
            return
        try:
            onset_expr, offset_expr, var_list = espresso.expression_to_cubes(expr_str)
            espresso.offset = offset_expr
            onset = onset_expr
            width = len(var_list)
            input_desc = f"expression: {expr_str}"
        except Exception as e:
            console.print(f"[red]Error parsing expression: {e}[/red]")
            return

    elif input_choice == '1':
        # Truth table CSV file
        csv_files = sorted(Path('.').glob('*.csv'))
        if not csv_files:
            console.print("[red]No CSV files found in current directory[/red]")
            return
        csv_path = get_selection("Select a truth table CSV file", csv_files)
        if not csv_path:
            return
        try:
            onset, width = espresso.load_data(str(csv_path))
            # Count don't-cares for info
            dc_count = sum(
                1 for row in csv_path.read_text(encoding='utf-8').splitlines()[1:]
                if row.strip().endswith(',x')
            )
            input_desc = f"CSV: {csv_path.name}"
            if dc_count > 0:
                input_desc += f" ({dc_count} don't-care rows)"
        except Exception as e:
            console.print(f"[red]Error loading CSV: {e}[/red]")
            return

    elif input_choice == '2':
        # Built-in example
        names = [f"{name} ({desc})" for name, desc in BUILTIN_EXAMPLES]
        selected = get_selection("Select a built-in example", names)
        if not selected:
            return
        idx = names.index(selected)
        name, desc = BUILTIN_EXAMPLES[idx]
        if name.endswith('.csv'):
            try:
                onset, width = espresso.load_data(name)
                input_desc = f"CSV: {name} ({desc})"
            except Exception as e:
                console.print(f"[red]Error loading {name}: {e}[/red]")
                return
        else:
            try:
                onset_expr, offset_expr, var_list = espresso.expression_to_cubes(name)
                espresso.offset = offset_expr
                onset = onset_expr
                width = len(var_list)
                input_desc = f"expression: {name} ({desc})"
            except Exception as e:
                console.print(f"[red]Error parsing {name}: {e}[/red]")
                return

    elif input_choice == '3':
        console.print("[yellow]Goodbye![/yellow]")
        return

    else:
        console.print("[red]Invalid selection[/red]")
        return

    # --- Step 2: Target Cost (tau) ---
    console.print("\n[bold blue]Target Cost (tau):[/bold blue]")
    console.print("  Enter an integer to constrain the minimization cost.")
    console.print("  Press Enter to skip (no constraint - best result found).")
    tau_str = get_input("Target cost (or Enter to skip): ").strip()
    if tau_str == "":
        tau = None  # No constraint
    else:
        try:
            tau = int(tau_str)
        except ValueError:
            console.print("[red]Invalid tau value, skipping constraint[/red]")
            tau = None

    # --- Step 3: Run Minimization ---
    console.print(f"\n[bold]Running ESPRESSO minimization...[/bold]")
    # Convert None (no constraint) to a large number so the loop runs to max_count
    tau_for_engine = float('inf') if tau is None else tau
    try:
        sol_str, final_cost = espresso.run_minimization(onset, width, tau_for_engine)
    except Exception as e:
        console.print(f"[red]Error during minimization: {e}[/red]")
        return

    # --- Step 4: Display Results ---
    table = Table(title="Minimization Result")
    table.add_column("Property", style="bold cyan")
    table.add_column("Value", style="green")

    table.add_row("Input Source", input_desc)
    table.add_row("Target Cost (tau)", str(tau) if tau is not None else "(none)")
    table.add_row("Minimized Expression", f"f = {sol_str}")
    table.add_row("Final Cost", str(final_cost))
    console.print(table)

    # --- Step 5: Netlist Generation ---
    gen_netlist = get_input("\nGenerate SPICE-style netlist? (y/N): ").strip().lower()
    netlist_path = None
    netlist_text = None
    net_inputs = None
    net_outputs = None

    if gen_netlist == 'y':
        default_name = "netlist.txt"
        netlist_filename = get_input(
            f"Enter output netlist filename (default: {default_name}): "
        ).strip()
        if not netlist_filename:
            netlist_filename = default_name
        netlist_path = Path(netlist_filename)

        try:
            netlist_text, net_inputs, net_outputs = espresso.generate_netlist(sol_str)
            with open(netlist_path, 'w', encoding='utf-8') as f:
                f.write(netlist_text)
            table.add_row("Generated Netlist", str(netlist_path))
            console.print(table)
            console.print(f"\n[bold blue]Netlist Content ({netlist_path}):[/bold blue]")
            console.print(Panel(netlist_text, border_style="green"))
        except Exception as e:
            console.print(f"[red]Error generating netlist: {e}[/red]")
            console.print(table)

    # --- Step 6: Save result text file ---
    save_result = get_input("\nSave result to text file? (y/N): ").strip().lower()
    if save_result == 'y':
        default_name = "minimizer_result.txt"
        result_filename = get_input(
            f"Enter output filename (default: {default_name}): "
        ).strip()
        if not result_filename:
            result_filename = default_name
        try:
            result_text = (
                f"Input Source: {input_desc}\n"
                f"Target Cost (tau): {tau if tau is not None else 'none'}\n"
                f"Minimized Expression: f = {sol_str}\n"
                f"Final Cost: {final_cost}\n"
            )
            with open(result_filename, 'w', encoding='utf-8') as f:
                f.write(result_text)
            console.print(f"[green]Result saved to {result_filename}[/green]")
        except Exception as e:
            console.print(f"[red]Error saving result: {e}[/red]")

    # --- Step 7: Logic Simulator integration ---
    if netlist_text is not None:
        run_sim = get_input("\nRun Logic Simulator on this netlist? (y/N): ").strip().lower()
        if run_sim == 'y':
            sim_dir = Path('..') / 'Logic Simulator'
            if not sim_dir.exists():
                console.print("[red]Logic Simulator directory not found[/red]")
                return

            # Create temp stimulus CSV covering all input combinations
            tmpdir = Path(tempfile.mkdtemp())
            stimulus_path = tmpdir / 'stimulus.csv'
            with open(stimulus_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(net_inputs)
                for bits in itertools.product([0, 1], repeat=len(net_inputs)):
                    writer.writerow(list(bits))

            report_path = tmpdir / 'report.csv'
            sim_cmd = [
                sys.executable,
                str(sim_dir / 'combinational_logic_simulator.py'),
                '--netlist', str(netlist_path.resolve()),
                '--stimulus', str(stimulus_path),
                '--output', str(report_path),
            ]
            console.print(f"\n[bold]Running Logic Simulator...[/bold]")
            sim_result = subprocess.run(
                sim_cmd, capture_output=True, text=True, cwd=str(sim_dir)
            )
            if sim_result.returncode != 0:
                console.print(f"[red]Simulation error: {sim_result.stderr}[/red]")
            else:
                console.print(f"[green]Simulation complete.[/green]")
                try:
                    with open(report_path, newline='') as f:
                        reader = csv.reader(f)
                        header = next(reader)
                        sim_table = Table(title="Simulation Results")
                        for col in header:
                            sim_table.add_column(col)
                        for row in reader:
                            sim_table.add_row(*row)
                    console.print(sim_table)
                    console.print(f"[dim]Report saved to: {report_path}[/dim]")
                except Exception as e:
                    console.print(f"[red]Error reading simulation report: {e}[/red]")

    console.print("\n[green]Done![/green]")


if __name__ == '__main__':
    run_interactive_minimizer()