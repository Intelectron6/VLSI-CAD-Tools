"""
Interactive TUI for the FSM State and Logic Minimizer.

Uses prompt_toolkit for interactive menus and rich for colored output.
Mirrors the user-friendly patterns from run_minimizer.py in the
Combinational Logic Minimizer project.

Usage:
    python run_fsm_minimizer.py          (interactive TUI)
    python fsm_minimizer.py              (CLI with hardcoded fsm.csv)
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

import pandas as pd

import fsm_minimizer
import fsm_parser
import fsm_netlist
# import fsm_diagram  # Temporarily disabled - diagrams will be re-enabled later

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


BUILTIN_EXAMPLES = [
    ("examples/fsm.csv", "6-state FSM with inputs 0,1"),
    ("examples/fsm2.csv", "6-state FSM with inputs 0,1,10,11 (multi-bit)"),
    ("examples/fsm.json", "6-state FSM from JSON (matches fsm.csv)"),
    ("examples/fsm2.json", "6-state FSM from JSON (matches fsm2.csv)"),
]


def run_interactive_minimizer():
    console.print(Panel.fit(
        "[bold cyan]ESPRESSO FSM State & Logic Minimizer - Interactive TUI[/bold cyan]",
        border_style="cyan"
    ))

    # --- Step 1: Select Input Type ---
    console.print("\n[bold blue]Select Input Type:[/bold blue]")
    console.print("  0: Truth Table CSV File")
    console.print("  1: JSON FSM File")
    console.print("  2: Built-in Example")
    console.print("  3: Exit")
    input_choice = get_input("Enter the number: ").strip()

    stt_df = None
    input_desc = ""

    if input_choice == '0':
        # Truth table CSV file
        csv_files = sorted(Path('.').glob('*.csv')) + sorted(Path('examples').glob('*.csv'))
        if not csv_files:
            console.print("[red]No CSV files found[/red]")
            return
        csv_path = get_selection("Select a truth table CSV file", csv_files)
        if not csv_path:
            return
        try:
            stt_df = pd.read_csv(str(csv_path))
            input_desc = f"CSV: {csv_path}"
        except Exception as e:
            console.print(f"[red]Error loading CSV: {e}[/red]")
            return

    elif input_choice == '1':
        # JSON FSM file
        json_files = sorted(Path('.').glob('*.json'))
        if not json_files:
            json_files = sorted(Path('examples').glob('*.json'))
        if not json_files:
            console.print("[red]No JSON files found[/red]")
            return
        json_path = get_selection("Select a JSON FSM file", json_files)
        if not json_path:
            return
        try:
            stt_df = fsm_parser.json_to_dataframe(str(json_path))
            input_desc = f"JSON: {json_path}"
        except Exception as e:
            console.print(f"[red]Error parsing JSON: {e}[/red]")
            return

    elif input_choice == '2':
        # Built-in example
        names = [f"{name} ({desc})" for name, desc in BUILTIN_EXAMPLES]
        selected = get_selection("Select a built-in example", names)
        if not selected:
            return
        idx = names.index(selected)
        name, desc = BUILTIN_EXAMPLES[idx]
        try:
            if name.endswith('.csv'):
                stt_df = pd.read_csv(name)
                input_desc = f"CSV: {name} ({desc})"
            elif name.endswith('.json'):
                stt_df = fsm_parser.json_to_dataframe(name)
                input_desc = f"JSON: {name} ({desc})"
        except Exception as e:
            console.print(f"[red]Error loading example: {e}[/red]")
            return

    elif input_choice == '3':
        console.print("[yellow]Goodbye![/yellow]")
        return

    else:
        console.print("[red]Invalid selection[/red]")
        return

    # Show input summary
    console.print(f"\n[bold]Input Summary:[/bold]")
    console.print(f"  Rows (transitions): {len(stt_df)}")
    console.print(f"  States: {sorted(stt_df['PS'].unique())}")
    console.print(f"  Inputs: {sorted(stt_df['x'].unique())}")
    console.print(f"  Outputs: {sorted(stt_df['z'].unique())}")

    # --- Step 2: Target Cost (tau) ---
    console.print("\n[bold blue]Target Cost (tau):[/bold blue]")
    console.print("  Enter an integer to constrain the minimization cost.")
    console.print("  Applied to all next-state and output logic functions.")
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
    tau_for_engine = float('inf') if tau is None else tau
    try:
        result = fsm_minimizer.run_minimization(stt_df, tau_for_engine)
    except Exception as e:
        console.print(f"[red]Error during minimization: {e}[/red]")
        return

    # --- Step 4: Display Results ---
    table = Table(title="FSM Minimization Result")
    table.add_column("Property", style="bold cyan")
    table.add_column("Value", style="green")

    table.add_row("Input Source", input_desc)
    table.add_row("Target Cost (tau)", str(tau) if tau is not None else "(none)")
    table.add_row("Final States", ", ".join(result['final_states']))
    table.add_row("Num States", str(len(result['final_states'])))
    table.add_row("Max Cost (Critical Path)", str(result['max_cost']))
    console.print(table)

    # Show individual expressions
    console.print(f"\n[bold blue]Minimized Expressions:[/bold blue]")
    for i, expr in enumerate(result['expressions']):
        console.print(f"  out[{i}]: f = {expr}")
        console.print(f"  Cost: {result['costs'][i]}")

    # --- Step 5: Netlist Generation ---
    gen_netlist = get_input("\nGenerate SPICE-style netlist? (y/N): ").strip().lower()
    netlist_path = None
    netlist_text = None

    if gen_netlist == 'y':
        default_name = "fsm_netlist.txt"
        netlist_filename = get_input(
            f"Enter output netlist filename (default: {default_name}): "
        ).strip()
        if not netlist_filename:
            netlist_filename = default_name
        netlist_path = Path(netlist_filename)

        try:
            netlist_text = fsm_netlist.generate_fsm_netlist(
                result, netlist_path=str(netlist_path)
            )
            table.add_row("Generated Netlist", str(netlist_path))
            console.print(table)
            console.print(f"\n[bold blue]Netlist Content ({netlist_path}):[/bold blue]")
            console.print(Panel(netlist_text, border_style="green"))
        except Exception as e:
            console.print(f"[red]Error generating netlist: {e}[/red]")
            console.print(table)

    # --- Step 5: State Transition Diagrams (TEMPORARILY DISABLED) ---
    # Diagrams will be re-enabled after arrow rendering is fixed.
    # Code is preserved in fsm_diagram.py for future use.
    gen_diagrams = 'n'  # Disabled for now

    # if gen_diagrams == 'y':
    #     default_prefix = "fsm_diagrams"
    #     diagram_prefix = get_input(
    #         f"Enter output prefix (default: {default_prefix}): "
    #     ).strip()
    #     if not diagram_prefix:
    #         diagram_prefix = default_prefix
    #     diagram_format = get_input(
    #         "Output format (png/pdf/svg, default: png): "
    #     ).strip()
    #     if not diagram_format:
    #         diagram_format = 'png'

    #     try:
    #         # Generate initial diagram
    #         initial_path = f"{diagram_prefix}_initial"
    #         fsm_diagram.generate_initial_diagram(
    #             stt_df, initial_path, "Initial FSM", format=diagram_format
    #         )

    #         # Generate reduced diagram
    #         reduced_path = f"{diagram_prefix}_reduced"
    #         fsm_diagram.generate_reduced_diagram(
    #             result, stt_df, reduced_path, "Reduced FSM", format=diagram_format
    #         )

    #         diagram_path = diagram_prefix
    #         table.add_row("Generated Diagrams", f"{diagram_prefix}_initial.{diagram_format}, {diagram_prefix}_reduced.{diagram_format}")
    #         console.print(table)
    #         console.print(f"[green]Diagrams saved with prefix: {diagram_prefix}[/green]")
    #     except Exception as e:
    #         console.print(f"[red]Error generating diagrams: {e}[/red]")

    # --- Step 6: Save result text file ---
    save_result = get_input("\nSave result to text file? (y/N): ").strip().lower()
    if save_result == 'y':
        default_name = "fsm_minimizer_result.txt"
        result_filename = get_input(
            f"Enter output filename (default: {default_name}): "
        ).strip()
        if not result_filename:
            result_filename = default_name
        try:
            result_text = (
                f"Input Source: {input_desc}\n"
                f"Target Cost (tau): {tau if tau is not None else 'none'}\n"
                f"Final States: {', '.join(result['final_states'])}\n"
                f"Max Cost: {result['max_cost']}\n"
                f"\nExpressions:\n"
            )
            for i, expr in enumerate(result['expressions']):
                result_text += f"  out[{i}]: f = {expr} (cost: {result['costs'][i]})\n"
            with open(result_filename, 'w', encoding='utf-8') as f:
                f.write(result_text)
            console.print(f"[green]Result saved to {result_filename}[/green]")
        except Exception as e:
            console.print(f"[red]Error saving result: {e}[/red]")

    console.print("\n[green]Done![/green]")


if __name__ == '__main__':
    run_interactive_minimizer()