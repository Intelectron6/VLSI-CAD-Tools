import re
import sys
import numpy as np
import pandas as pd
import random
import argparse

from sympy import parse_expr, to_dnf, And, Or, Not, Symbol

# ---------------- ESPRESSO engine (unchanged) ----------------

def encoding(x):
    x = str(x)
    if (x == '0'):
        y,z = 1,0
    elif (x == '1'):
        y,z = 0,1
    elif (x == 'x'):
        y,z = 1,1
    else:
        y,z = 0,0
    return y,z

def calc_weights(theset):
    theset_trps = np.array(theset).T
    #print("Input to calc_weights:", theset)
    #print("Input to calc_weights transposed:",theset_trps)
    colsums = []
    for i in range(len(theset_trps)):
        for j in range(len(theset_trps[i])):
            colsums.append(sum(theset_trps[i][j]))

    colsums = np.array(colsums)

    theset_mod = []
    weights = []
    for i in range(len(theset)):
        theset_mod.append([])
        for j in range(len(theset[i])):
            theset_mod[i] = theset_mod[i] + list(theset[i][j])

    for i in range(len(theset)):
        weights.append(np.dot(colsums,np.array(theset_mod[i])))
    #print(weights)
    return weights

def intersection(cube1, cube2):
    inter = []
    for i in range(len(cube1)):
        inter.append([])
        if (cube1[i] == (0,0) and cube2[i] == (0,0)):
            inter[i] = (0,0)
        elif (cube1[i] == (0,1) and cube2[i] == (0,0)):
            inter[i] = (0,0)
        elif (cube1[i] == (1,0) and cube2[i] == (0,0)):
            inter[i] = (0,0)
        elif (cube1[i] == (1,1) and cube2[i] == (0,0)):
            inter[i] = (0,0)
        elif (cube1[i] == (0,0) and cube2[i] == (0,1)):
            inter[i] = (0,0)
        elif (cube1[i] == (0,1) and cube2[i] == (0,1)):
            inter[i] = (0,1)
        elif (cube1[i] == (1,0) and cube2[i] == (0,1)):
            inter[i] = (0,0)
        elif (cube1[i] == (1,1) and cube2[i] == (0,1)):
            inter[i] = (0,1)
        elif (cube1[i] == (0,0) and cube2[i] == (1,0)):
            inter[i] = (0,0)
        elif (cube1[i] == (0,1) and cube2[i] == (1,0)):
            inter[i] = (0,0)
        elif (cube1[i] == (1,0) and cube2[i] == (1,0)):
            inter[i] = (1,0)
        elif (cube1[i] == (1,1) and cube2[i] == (1,0)):
            inter[i] = (1,0)
        elif (cube1[i] == (0,0) and cube2[i] == (1,1)):
            inter[i] = (0,0)
        elif (cube1[i] == (0,1) and cube2[i] == (1,1)):
            inter[i] = (0,1)
        elif (cube1[i] == (1,0) and cube2[i] == (1,1)):
            inter[i] = (1,0)
        else:
            inter[i] = (1,1)
    return inter

def supercube(cube1, cube2):
    inter = []
    for i in range(len(cube1)):
        inter.append([])
        if (cube1[i] == (0,0) and cube2[i] == (0,0)):
            inter[i] = (0,0)
        elif (cube1[i] == (0,1) and cube2[i] == (0,0)):
            inter[i] = (0,1)
        elif (cube1[i] == (1,0) and cube2[i] == (0,0)):
            inter[i] = (1,0)
        elif (cube1[i] == (1,1) and cube2[i] == (0,0)):
            inter[i] = (1,1)
        elif (cube1[i] == (0,0) and cube2[i] == (0,1)):
            inter[i] = (0,1)
        elif (cube1[i] == (0,1) and cube2[i] == (0,1)):
            inter[i] = (0,1)
        elif (cube1[i] == (1,0) and cube2[i] == (0,1)):
            inter[i] = (1,1)
        elif (cube1[i] == (1,1) and cube2[i] == (0,1)):
            inter[i] = (1,1)
        elif (cube1[i] == (0,0) and cube2[i] == (1,0)):
            inter[i] = (1,0)
        elif (cube1[i] == (0,1) and cube2[i] == (1,0)):
            inter[i] = (1,1)
        elif (cube1[i] == (1,0) and cube2[i] == (1,0)):
            inter[i] = (1,0)
        elif (cube1[i] == (1,1) and cube2[i] == (1,0)):
            inter[i] = (1,1)
        elif (cube1[i] == (0,0) and cube2[i] == (1,1)):
            inter[i] = (1,1)
        elif (cube1[i] == (0,1) and cube2[i] == (1,1)):
            inter[i] = (1,1)
        elif (cube1[i] == (1,0) and cube2[i] == (1,1)):
            inter[i] = (1,1)
        else:
            inter[i] = (1,1)
    return inter

def complement(theset):
    compset = []
    for i in theset:
        if i == (0,0):
            noti = (1,1)
        elif i == (0,1):
            noti = (1,0)
        elif i == (1,0):
            noti = (0,1)
        else:
            noti = (0,0)
        compset.append(noti)
    return compset

def expand(onset, choice):
    no_intersect_count=0
    inter=[]
    for i in range(len(onset[choice])):
        memory = onset[choice][i]
        onset[choice][i] = (1,1)
        inter.clear()
        no_intersect_count=0
        for j in range(len(offset)):
            inter.append(intersection(onset[choice], offset[j]))
            if((0,0) in inter[j]):
                no_intersect_count = no_intersect_count + 1
        if (no_intersect_count == len(offset)):
            useless = 0
            #print("Valid expansion!")
        else:
            #print("Invalid expansion...")
            onset[choice][i] = memory 
        #print("inter in expansion",inter)
        #print("count ", no_intersect_count)
    return onset

def irredundant(onset, choice):
    inter = []
    ttlgychk = []
    all_ones = []
    removed_stuff = []
    for i in range(len(onset)):
        if (i != choice):
            inter.append(intersection(onset[choice], onset[i]))
        else:
            inter.append("Dummy value")
    for i in range(len(onset)):
        if (i != choice):
            ttlgychk.append(supercube(complement(onset[i]), inter[i]))
        else:
            ttlgychk.append("Dummy value")

    nvar = len(onset[0])    
    all_ones = [(1,1) for i in range(nvar)]

    #print("Intersection:", inter)
    #print("Tautology check:", ttlgychk)
    #print("All ones", all_ones)

    for i in range(len(onset)):
        if (i != choice):
            if (ttlgychk[i] == all_ones):
                #print("There is redundancy, remove minterm",i)
                removed_stuff.append(onset[i])
            else:
                useless = 0
                #print("No redundancy here...")
    for i in removed_stuff:
        onset.remove(i)
    return onset

def reduce(onset, choice, counter):
    num = counter // 50
    count=0
    onset_inter=[]
    for i in range(len(onset[choice]) - num):
        if (onset[choice][i] == (1,1)):
            count=count+1
            onset[choice][i]=(0,1)
            new_term=onset[choice].copy()
            new_term[i]=(1,0)
            if(count>1):
                 for j in range(count-1):
                    onset_inter[j][i]=(0,1)
                 for j in range(count-1):
                    new_term1= onset_inter[j].copy()
                    new_term1[i]=(1,0)
                    onset_inter.append(new_term1)

            onset_inter.append(new_term)
            #print(onset_inter)

    if (len(onset_inter) != 0):
        for i in range(len(onset_inter)):        
            onset.append(onset_inter[i])
    return onset

def calc_cost(onset):
    cost = len(onset)
    max = 0
    for i in range(len(onset)):
        sum = 0
        for j in range(len(onset[i])):
            if onset[i][j] != (1,1):
                sum = sum + 1
        if (sum > max):
            max = sum      
    return cost + max

# ---------------- Module-level state (read by expand) ----------------

offset = None  # populated by load_data(); read by expand()

# ---------------- Data loading & validation ----------------

def load_data(input_path):
    """Read a truth-table CSV, validate it, and populate module-level offset.

    Expected columns: x{width-1}, ..., x1, x0, f  (e.g. x2,x1,x0,f)
    Cell values must be 0, 1, or x (don't-care).

    Returns (onset, width) where onset is the list of input cubes for f=1.
    """
    global offset

    tt = pd.read_csv(input_path)

    # Identify input columns (x0, x1, ...) and the output column (f)
    x_cols = sorted(
        [c for c in tt.columns if str(c).startswith('x')],
        key=lambda c: int(str(c)[1:])
    )
    if 'f' not in tt.columns:
        raise ValueError(f"CSV must contain an 'f' output column. Found: {list(tt.columns)}")
    if not x_cols:
        raise ValueError(f"CSV must contain at least one xN input column. Found: {list(tt.columns)}")

    width = len(x_cols)

    # Validate cell values
    valid = {'0', '1', 'x'}
    for col in x_cols + ['f']:
        bad = tt[~tt[col].astype(str).isin(valid)][col].unique()
        if len(bad) > 0:
            raise ValueError(
                f"Column '{col}' contains invalid values {list(bad)}. "
                f"Allowed values are 0, 1, x."
            )

    length = len(tt)

    # Build the encoded matrix: [input cubes..., f]
    mat = []
    for i in range(length):
        row = []
        for j in range(width):
            # columns are ordered x{width-1} ... x0; match original indexing
            col_name = 'x' + str(width - j - 1)
            row.append(encoding(tt[col_name][i]))
        row.append(str(tt['f'][i]))
        mat.append(row)

    onset, offset_local, dcset = [], [], []
    for i in range(length):
        if mat[i][-1] == '0':
            offset_local.append(mat[i][0:-1])
        elif mat[i][-1] == '1':
            onset.append(mat[i][0:-1])
        else:
            dcset.append(mat[i][0:-1])

    offset = offset_local  # module-level, read by expand()
    return onset, width

# ---------------- Expression builder (unchanged logic) ----------------

def cubes_to_expression(sol_set):
    """Convert a list of cubes into the SOP expression string (original logic)."""
    sol_str = ''
    for i in sol_set:
        count = 0
        sol_str = sol_str + '('
        another_count = 0
        for j in i:
            if (j == (0, 1)):
                another_count = another_count + 1
                if (another_count > 1):
                    sol_str = sol_str + ' AND '
                sol_str = sol_str + "x["+str(count)+"]"
            elif (j == (1, 0)):
                another_count = another_count + 1
                if (another_count > 1):
                    sol_str = sol_str + ' AND '
                sol_str = sol_str + "(NOT x["+str(count)+"])"
            count = count + 1
        sol_str = sol_str + ') OR '
    sol_str = sol_str[:-3]
    return sol_str

# ---------------- Symbolic expression -> cubes (Phase 2) ----------------

def parse_bool_expression(expr_str):
    """Parse a boolean expression string into a sympy expression.

    Accepts forms like:
        'A & B | ~C'          (symbolic operators)
        'A AND B OR NOT C'    (word operators)
        'A.B + A.!B'          (EE notation: . = AND, + = OR, ! = NOT)
        'f = A & B | ~C'      (with optional 'f =' prefix)

    Word operators AND/OR/NOT (case-insensitive) are converted to &/|/~.
    """
    s = expr_str.strip()

    # Strip optional 'f = ' / 'F = ' prefix (with optional spaces)
    s = re.sub(r'^[fF]\s*=\s*', '', s)

    # EE notation: replace '!(' with '~(' (NOT of parenthesized expression)
    # Must be done BEFORE dot replacement
    s = s.replace('!(', '~(')
    # EE notation: replace '!' before a variable with '~' (NOT)
    s = re.sub(r'!(\w)', r'~\1', s)

    # EE notation: replace '.' between word characters with '&' (AND)
    # Handles both 'A.B' -> 'A&B' and 'A.~B' -> 'A&~B'
    s = re.sub(r'(\w)\.(~?\w)', r'\1&\2', s)

    # EE notation: replace '+' with '|' (OR)
    s = s.replace('+', '|')

    # Word operators (case-insensitive, whole word)
    s = re.sub(r'\bAND\b', '&', s, flags=re.IGNORECASE)
    s = re.sub(r'\bOR\b', '|', s, flags=re.IGNORECASE)
    s = re.sub(r'\bNOT\b', '~', s, flags=re.IGNORECASE)

    expr = parse_expr(s)
    return expr


def _dnf_to_cubes(dnf, var_index):
    """Convert a sympy DNF expression into a list of cubes.

    Each cube is a list of (y,z) tuples:
        (0, 1) = positive literal  (x)
        (1, 0) = negative literal  (NOT x)
        (1, 1) = don't-care        (variable absent from term)

    Contradictory terms (e.g. B & ~B) are skipped since they are always false.
    """
    width = len(var_index)
    if isinstance(dnf, Or):
        terms = dnf.args
    else:
        terms = [dnf]

    cubes = []
    for term in terms:
        if isinstance(term, And):
            literals = term.args
        else:
            literals = [term]

        cube = [(1, 1)] * width
        contradictory = False
        for lit in literals:
            if isinstance(lit, Not):
                var = str(lit.args[0])
                polarity = 'neg'
            else:
                var = str(lit)
                polarity = 'pos'

            if var in var_index:
                idx = var_index[var]
                desired = (0, 1) if polarity == 'pos' else (1, 0)
                # Detect contradiction: variable already assigned opposite polarity
                if cube[idx] != (1, 1) and cube[idx] != desired:
                    contradictory = True
                    break
                cube[idx] = desired

        if contradictory:
            continue  # Skip always-false terms like B & ~B

        cubes.append(cube)

    return cubes


def expression_to_cubes(expr_str):
    """Convert a boolean expression string into onset and offset cubes.

    Parses the expression, converts to Disjunctive Normal Form (DNF), and maps
    each conjunction term to a cube in the internal representation:
        (0, 1) = positive literal  (x)
        (1, 0) = negative literal  (NOT x)
        (1, 1) = don't-care        (variable absent from term)

    The offset set (f = 0) is derived from the expression's complement using
    sympy, so no truth-table enumeration is needed.

    Returns (onset, offset, var_list) where onset/offset are lists of cubes
    and var_list is the ordered list of variable names (mapped to x[0], x[1], ...).
    """
    expr = parse_bool_expression(expr_str)

    # Collect and order variables deterministically
    var_list = sorted(expr.atoms(Symbol), key=lambda sym: str(sym))
    var_index = {str(v): i for i, v in enumerate(var_list)}

    # Onset: DNF of the expression
    onset_dnf = to_dnf(expr)
    onset = _dnf_to_cubes(onset_dnf, var_index)

    # Offset: DNF of the complement (f = 0 regions)
    offset_dnf = to_dnf(~expr)
    offset = _dnf_to_cubes(offset_dnf, var_index)

    return onset, offset, var_list


# ---------------- Netlist Generator (Phase 3) ----------------

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

    Each term is a list of literals. Each literal is (var_idx, is_negated).
    Expression format: 'f = (x[1]) OR (x[0] AND x[2])'
    """
    s = re.sub(r'^[fF]\s*=\s*', '', expr_str.strip())

    # Split by top-level OR
    terms_str = split_top_level(s, ' OR ')

    terms = []
    for term_str in terms_str:
        term_str = term_str.strip()

        # Strip outer parentheses (may be nested like ((NOT x[0]) AND x[1]))
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
                var_str = lit_str[4:].strip()
                is_negated = True
            else:
                var_str = lit_str
                is_negated = False

            # Extract index from x[N]
            m = re.match(r'x\[(\d+)\]', var_str)
            if not m:
                raise ValueError(f"Cannot parse literal: {lit_str}")
            var_idx = int(m.group(1))

            literals.append((var_idx, is_negated))

        terms.append(literals)

    return terms


def generate_netlist(expr_str, output_node='f'):
    """Generate a SPICE-style netlist from a minimized SOP expression.

    Uses only 2-input gates supported by the Logic Simulator:
    NOT, BUFF, AND, OR, NAND, NOR, XOR, XNOR, MUX2x1.

    Returns (netlist_text, input_nodes, output_nodes).
    """
    terms = parse_sop_terms(expr_str)

    # Collect all variable indices used
    all_vars = sorted(set(
        var_idx for term in terms for var_idx, _ in term
    ))

    input_nodes = [f'x[{i}]' for i in all_vars]
    output_nodes = [output_node]

    lines = []
    lines.append('input ' + ' '.join(input_nodes))
    lines.append('output ' + ' '.join(output_nodes))

    # Node counter for intermediate signals
    node_counter = [0]

    def new_node():
        node_counter[0] += 1
        return f'n{node_counter[0]}'

    # NOT gate cache: variable index -> node name (for negated literals)
    not_cache = {}

    def get_not_output(var_idx):
        """Get or create a NOT gate output for a negated variable."""
        if var_idx not in not_cache:
            not_out = new_node()
            lines.append(f'NOT x[{var_idx}] {not_out}')
            not_cache[var_idx] = not_out
        return not_cache[var_idx]

    # Process each term: AND of literals (2-input AND gates only)
    term_outputs = []
    for term in terms:
        # Convert literals to node names
        lit_nodes = []
        for var_idx, is_negated in term:
            if is_negated:
                lit_nodes.append(get_not_output(var_idx))
            else:
                lit_nodes.append(f'x[{var_idx}]')

        # Build AND tree with 2-input AND gates
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
        if term_out.startswith('x['):
            # Raw input literal passthrough
            lines.append(f'BUFF {term_out} {output_node}')
        else:
            # Intermediate node passthrough
            lines.append(f'BUFF {term_out} {output_node}')
    else:
        current = term_outputs[0]
        for k in range(1, len(term_outputs)):
            out = output_node if k == len(term_outputs) - 1 else new_node()
            lines.append(f'OR {current} {term_outputs[k]} {out}')
            current = out

    netlist_text = '\n'.join(lines) + '\n'
    return netlist_text, input_nodes, output_nodes


# ---------------- Minimization loop (unchanged logic) ----------------

def run_minimization(onset, width, tau):
    """Run the ESPRESSO expand/reduce/irredundant loop until cost <= tau.

    Returns (expression_string, final_cost).
    """
    max_count = int(width * 50)

    # Expansion process
    weights = calc_weights(onset)
    choice_exp = weights.index(min(weights))
    onset = expand(onset, choice_exp)

    # Irredundancy process
    onset = irredundant(onset, choice_exp)

    # Cost calculation
    cost = calc_cost(onset)

    count = 0
    prev_cost = cost
    sol_set = onset
    prev_weights = weights

    while (cost > tau and count < max_count):
        # Reduction process
        red_weights = calc_weights(onset)
        choice_red = red_weights.index(max(red_weights))
        onset = reduce(onset, choice_red, count)

        exp_weights = calc_weights(onset)
        if (exp_weights == prev_weights):
            choice_exp = random.choice([k for k in range(len(onset))])
        else:
            choice_exp = exp_weights.index(min(exp_weights))

        prev_weights = exp_weights

        onset = expand(onset, choice_exp)

        # Irredundancy process
        onset = irredundant(onset, choice_exp)

        # Cost calculation
        cost = calc_cost(onset)

        if (cost < prev_cost):
            prev_cost = cost
            sol_set = onset

        count = count + 1

    sol_str = cubes_to_expression(sol_set)
    return sol_str, prev_cost

# ---------------- CLI entry point ----------------

def main():
    parser = argparse.ArgumentParser(
        description='ESPRESSO-based 2-level combinational logic minimizer.'
    )
    parser.add_argument(
        '--input', default='logic.csv',
        help='Path to truth-table CSV (default: logic.csv)'
    )
    parser.add_argument(
        '--expression', default=None,
        help='Boolean expression string (e.g. "A & B | ~C"). '
             'Overrides --input when provided.'
    )
    parser.add_argument(
        '--tau', type=int, default=None,
        help='Target cost. If omitted, you will be prompted interactively.'
    )
    parser.add_argument(
        '--output', default=None,
        help='Path to save the result text file (default: print only)'
    )
    parser.add_argument(
        '--netlist', default=None,
        help='Path to save the generated SPICE-style netlist (default: no netlist)'
    )
    args = parser.parse_args()

    # ---------------- Input path: expression or truth-table CSV ----------------
    global offset  # module-level, read by expand()

    if args.expression is not None:
        try:
            onset_expr, offset_expr, var_list = expression_to_cubes(args.expression)
        except Exception as e:
            print(f"Error: failed to parse boolean expression: {e}")
            sys.exit(1)
        offset = offset_expr
        onset = onset_expr
        width = len(var_list)
        input_desc = f'expression: {args.expression}'
    else:
        onset, width = load_data(args.input)
        input_desc = f'CSV: {args.input}'

    if args.tau is None:
        tau = int(input("Enter target cost:"))
    else:
        tau = args.tau

    sol_str, final_cost = run_minimization(onset, width, tau)

    result_text = (
        f"Input: {input_desc}\n"
        "Minimized Expression:\n"
        "f = " + sol_str + "\n"
        "Final cost: " + str(final_cost) + "\n"
    )
    print(result_text)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(result_text)
        print(f"Result saved to {args.output}")

    if args.netlist:
        netlist_text, net_inputs, net_outputs = generate_netlist(sol_str)
        with open(args.netlist, 'w', encoding='utf-8') as f:
            f.write(netlist_text)
        print(f"Netlist saved to {args.netlist}")

if __name__ == '__main__':
    main()