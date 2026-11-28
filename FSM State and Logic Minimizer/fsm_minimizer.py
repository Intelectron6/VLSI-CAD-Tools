import numpy as np
import pandas as pd
import math
import random

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
            random_useless_value = 0
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
                random_useless_value = 0
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
    maxval = 0
    for i in range(len(onset)):
        sumval = 0
        for j in range(len(onset[i])):
            if onset[i][j] != (1,1):
                sumval = sumval + 1
        if (sumval > maxval):
            maxval = sumval      
    return cost + maxval

def fsm_minimizer(class_eq_st, length, factor, stt_df):
    record = dict()
    for i,a in enumerate(class_eq_st):
            record[a] = []

    #Step 1
    for i in range(length):
        prst = stt_df['PS'][i] 
        outp = stt_df['z'][i]
        for j in class_eq_st:
            if (j == prst):
                record[prst].append(outp)


    vals = list(record.values())
    vals_short = []

    for i in vals:
        if i in vals_short:
            continue
        else:
            vals_short.append(i)            

    class_eq_st2 = []
    for i in range(len(vals_short)):
        class_eq_st2.append([])

    for i in range(length//factor):
        for j in range(len(vals_short)):
            if(record[class_eq_st[i]] == vals_short[j]):
                class_eq_st2[j].append(class_eq_st[i])
            
    #print(class_eq_st2)
    prev_class_eq = []

    behav = dict()
    for i,a in enumerate(class_eq_st):
            behav[a] = []

    #Step 2
    while(class_eq_st2 != prev_class_eq):
        prev_class_eq = class_eq_st2.copy()
        for i in class_eq_st2:
            for j in range(len(i)):
                for k in range(length):
                    if (i[j] == stt_df['PS'][k]):
                        for l,b in enumerate(class_eq_st2):  
                            if (stt_df['NS'][k] in b):
                                behav[i[j]].append(l)
        new_class = []

        for i in class_eq_st2:
            first = behav[i[0]]
            for j in range(1,len(i)):
                if (behav[i[j]] != first):
                    new_class.append(i[j])
                    i.remove(i[j])

        if (new_class != []):            
            class_eq_st2.append(new_class)
        
        
    print("Equivalanet states:", class_eq_st2)

    final_states = []
    for i in range(len(class_eq_st2)):
        final_states.append("S"+str(i))

    print("Final states:", final_states)

    # Build state mapping from old states to new state names
    state_mapping = {}
    for new_idx, old_states in enumerate(class_eq_st2):
        for old_state in old_states:
            state_mapping[old_state] = f"S{new_idx}"

    #Updating the state transition table    	 
    old_x = stt_df['x']
    old_PS = stt_df['PS']
    old_NS = stt_df['NS']
    old_z = stt_df['z']

    whatever_x = list(old_x)
    stuff_x = len(str(max(whatever_x)))

    for i in range(len(whatever_x)):
        if (len(str(whatever_x[i])) < stuff_x):
            whatever_x[i] = '0'*(stuff_x - len(str(whatever_x[i]))) + str(whatever_x[i])             

    whatever_z = list(old_z)
    stuff_z = len(str(max(whatever_z)))

    for i in range(len(whatever_z)):
        if (len(str(whatever_z[i])) < stuff_z):
            whatever_z[i] = '0'*(stuff_z - len(str(whatever_z[i]))) + str(whatever_z[i])             
               
    new_PS = []
    new_NS = []

    #Encoding the states
    encoded_states = []
    width = str(math.ceil(np.log2(len(final_states))))
    form = '{0:0'+width+'b}'
    for i in range(len(final_states)):
        encoded_states.append(form.format(i))

    print("Encoded states:", encoded_states)

    for i,a in enumerate(old_PS):
        for j,b in enumerate(class_eq_st2):
            if a in b:
                new_PS.append(encoded_states[j])

    for i,a in enumerate(old_NS):
        for j,b in enumerate(class_eq_st2):
            if a in b:
                new_NS.append(encoded_states[j])

    tt_inputs = []
    tt_outputs = []
    for i in range(length):
        new_ipe = str(whatever_x[i]) + new_PS[i]
        new_ope = str(whatever_z[i]) + new_NS[i]
        if (new_ipe in tt_inputs):
            continue
        else:
            tt_inputs.append(new_ipe)
            tt_outputs.append(new_ope)

    indexing = []
    new_length = len(tt_inputs)

    for i in range(new_length):
        indexing.append(int(tt_inputs[i],2))
        
    for i in range(new_length-1):
        for j in range(new_length-1-i):
            if indexing[i] > indexing[i+1]:
                tt_inputs[i+1], tt_inputs[i] = tt_inputs[i], tt_inputs[i+1]
                tt_outputs[i+1], tt_outputs[i] = tt_outputs[i], tt_outputs[i+1]

    #print("Inputs:", tt_inputs)
    #print("Outputs:", tt_outputs)

    no_outps = len(tt_outputs[0])
    no_inps = len(tt_inputs[0])
    outps_indv = []
    outps_indv2 = []
    for i in range(no_outps):
        outps_indv.append([])
        outps_indv2.append([])    

    for i in range(new_length):
        for j in range(no_outps):
            outps_indv[j].append(list(tt_outputs[i])[j])

    input_list = []
    for i in tt_inputs:
        input_list.append(list(i))

    output_list = []
    for i in tt_outputs:
        output_list.append(list(i))

    var_len = len(output_list)
    op_len = len(output_list[0])

    truth_tables = []

    for i in range(var_len):
        new_list = input_list[i]
        for j in range(op_len):
            new_list.append(output_list[i][j])
        truth_tables.append(new_list)

    tt = pd.DataFrame(truth_tables)
    return final_states, tt, class_eq_st2, state_mapping


# Module-level state (read by expand())
offset = None


def run_minimization(stt_df, target_cost):
    """Run FSM state minimization and logic synthesis from a transition table DataFrame.

    Parameters
    ----------
    stt_df : pandas.DataFrame
        DataFrame with columns 'x', 'PS', 'NS', 'z' (same format as the CSV input).
    target_cost : int
        Target cost for ESPRESSO minimization.

    Returns
    -------
    dict
        Dictionary with keys:
        - 'final_states': list of minimized state names
        - 'expressions': list of minimized SOP expression strings (one per output bit)
        - 'costs': list of final costs (one per output bit)
        - 'max_cost': maximum cost across all outputs (critical path delay)
        - 'transition_table': the minimized transition table DataFrame
        - 'inp_len': number of input bits
        - 'state_mapping': dict mapping old state names to new state names (e.g. {'A': 'S0', 'B': 'S1'})
    """
    stt = stt_df

    print("State Minimization")
    class_eq_st = list(stt['PS'])
    length = len(class_eq_st)
    inp_len = len(str(max(list(stt['x']))))
    factor = 2 * inp_len
    class_eq_st = class_eq_st[0:length // factor]
    print("Original states:", class_eq_st)

    final_states, tt, class_eq_st2, state_mapping = fsm_minimizer(class_eq_st, length, factor, stt)

    print("")
    cost_list = []
    expressions = []
    global offset  # module-level, read by expand()
    st_len = math.ceil(np.log2(len(final_states)))
    outp_len = len(str(max(list(stt['z']))))
    for k in range(st_len + outp_len):
        if k < st_len:
            print("Solutions to Next State Logic: NS(" + str(st_len - k - 1) + ")")
        else:
            print("Solutions to Output Logic Z(" + str(st_len + outp_len - k - 1) + ")")

        length = len(tt[st_len + outp_len + k])
        width = int(math.ceil(np.log2(length)))
        max_count = int(width * 50)

        mat = []
        for i in range(length):
            mat.append([])
            for j in range(width + 1):
                mat[i].append('00')

        for i in range(length):
            for j in range(width):
                mat[i][j] = encoding(tt[width - j - 1][i])
            mat[i][width] = tt[st_len + outp_len + k][i]

        onset, offset, dcset = [], [], []
        for i in range(length):
            if mat[i][-1] == '0':
                offset.append(mat[i][0:-1])
            elif mat[i][-1] == '1':
                onset.append(mat[i][0:-1])
            else:
                dcset.append(mat[i][0:-1])

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
        tau = target_cost

        while (cost > tau and count < max_count):
            # Reduction process
            red_weights = calc_weights(onset)
            choice_red = red_weights.index(max(red_weights))
            onset = reduce(onset, choice_red, count)

            exp_weights = calc_weights(onset)
            if exp_weights == prev_weights:
                choice_exp = random.choice([k for k in range(len(onset))])
            else:
                choice_exp = exp_weights.index(min(exp_weights))

            prev_weights = exp_weights

            onset = expand(onset, choice_exp)

            # Irredundancy process
            onset = irredundant(onset, choice_exp)

            # Cost calculation
            cost = calc_cost(onset)

            if cost < prev_cost:
                prev_cost = cost
                sol_set = onset

            count = count + 1

        sol_str = ''
        for i in sol_set:
            count = 0
            count1 = 0
            sol_str = sol_str + '('
            another_count = 0
            for j in i:
                if j == (0, 1):
                    another_count = another_count + 1
                    if another_count > 1:
                        sol_str = sol_str + ' AND '
                    if count < inp_len:
                        var = 'x'
                        count1 = count
                    else:
                        var = 'PS'
                        count1 = count - inp_len
                    sol_str = sol_str + var + "[" + str(count1) + "]"
                elif j == (1, 0):
                    another_count = another_count + 1
                    if another_count > 1:
                        sol_str = sol_str + ' AND '
                    if count < inp_len:
                        var = 'x'
                        count1 = count
                    else:
                        var = 'PS'
                        count1 = count - inp_len
                    sol_str = sol_str + "(NOT " + var + "[" + str(count1) + "])"
                count = count + 1
            sol_str = sol_str + ') OR '
        sol_str = sol_str[:-3]

        cost_list.append(prev_cost)
        expressions.append(sol_str)
        print(sol_str)
        print("Cost:", prev_cost)
        print("")

    return {
        'final_states': final_states,
        'expressions': expressions,
        'costs': cost_list,
        'max_cost': max(cost_list),
        'transition_table': tt,
        'inp_len': inp_len,
        'state_mapping': state_mapping,
    }


if __name__ == '__main__':
    stt = pd.read_csv("examples/fsm.csv")
    target = int(input("Enter target cost:"))
    result = run_minimization(stt, target)
    print("Maximum delay (critical path) =", result['max_cost'])
