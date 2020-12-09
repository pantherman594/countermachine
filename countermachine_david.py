#counter machine
#The low level code is a list of instructions.
#Each instruction is a string.
#The strings have the following format:
#I<let> (where <let> denotes any lower-case letter)
#D<let>
#B<let><n> where <n> denotes an integer constant--note that this is written
#without spaces
#B<n>
#H#

#The function below interprets the low-level code.  The second argument is
#a tuple of integers originally assigned to 'a','b',.... 

import string
import sys
letters='abcdefghijklmnopqrstuvwxyz'
Letters='ABCDEFGHIJKLMNOPQRSTUVWXYZ'
digits='0123456789'
alphanum=letters+Letters+digits+'_'

def allin(s,charset):
    for c in s:
        if not (c in charset):
            return False
    return True


def interpret(obj,*args,**kwargs):
    program, child_programs = obj
    counters=[0]*26

    for j in range(len(args)):
        counters[j]=args[j]

    macro = kwargs.pop('macro', False)
    verbose = not macro and kwargs.pop('verbose', False)
    very_verbose = kwargs.pop('very_verbose', False)
    if very_verbose:
        verbose = True

    # merge the program's child_programs with the given ones, if provided.
    child_programs.update(kwargs.pop('child_programs', {}))

    ip=0
    while program[ip]!='H':
        current_instruction = program[ip]
        if ip>len(program):
            sys.exit('instruction pointer out of range')
        if current_instruction[0] == 'I':
            variable=ord(current_instruction[1])-ord('a')
            counters[variable]+=1
            
            if verbose:
                print (str(ip)+': '+'inc '+current_instruction[1])
            ip+=1
        elif current_instruction[0]=='D':
            variable=ord(current_instruction[1])-ord('a')
            counters[variable]=max(0,counters[variable]-1)
            if verbose:
                print (str(ip)+': '+'dec '+current_instruction[1])
            ip+=1
            
        elif current_instruction[0]=='B' and (current_instruction[1] in letters):
            variable=ord(current_instruction[1])-ord('a')
            #print ip,variable
            target=int(current_instruction[2:])
            if verbose:
                print (str(ip)+': '+'goto ' + str(target) + ' if '+current_instruction[1]+'=0')
            if counters[variable]==0:
                ip=target
            else:
                ip+=1
            
        elif current_instruction[0]=='B':
            target=int(current_instruction[1:])
            if verbose:
                print (str(ip)+': '+'goto '+str(target))
            ip=target

        elif current_instruction[0]=='M':
            file, macro_counters = current_instruction[1:].split('#')

            if verbose:
                print(str(ip) + ': MACRO ' + file + ' ' + ' '.join(list(macro_counters)))

            macro_counters = [(ord(x) - ord('a') if x in letters else -1) for x in macro_counters]
            macro_counter_values = [(counters[x] if x >= 0 else 0) for x in macro_counters]

            # call the child program. pass the global child_programs down to it
            result = interpret(child_programs[file],
                               *macro_counter_values,
                               verbose=verbose,
                               very_verbose=very_verbose,
                               child_programs=child_programs,
                               macro=True)

            # copy the named counters back to the main counter program
            for i, variable in enumerate(macro_counters):
                if variable >= 0:
                    counters[variable] = result[i]

            ip+=1

        elif current_instruction[0]=='P':
            print(str(ip)+':', counters)
            ip+=1

        if verbose:
            print(counters)

    return counters

#A source program is here represented as a sequence of lines, each
#line a list of strings.  Assemble the source program into the lower-level
#code used above, and return the low-level program.

def assemble(source):
    symbol_table={}
    obj=[]
    current=0
    child_programs = {}

    for line in source:
        #is it a label?
        #These have the form alphanum*:
        if (len(line)==1) and (line[0][-1]==':') and allin(line[0][:-1],alphanum):
            #print 'label'
            label=line[0][:-1]
            if label in symbol_table:
                sys.exit('redefinition of label '+label)
            else:
                symbol_table[label]=current

        #is it a print instruction?
        #These have the form print
        if (len(line)==1) and (line[0]=='print'):
            #print 'print'
            obj.append('P')
            current+=1
                
        #is it a conditional branch instruction?
        #These have the form goto label if x=0 but the parser
        #accepts anything of form goto label if lower-case letter followd by anything.
        elif (len(line)>=4) and (line[0]=='goto') and allin(line[1],alphanum) and (line[2]=='if') and (line[3][0] in letters):
            #print 'conditional branch'
            label=line[1]
            variable=line[3][0]
            obj.append('B'+variable+'#'+label)
            current+=1
        
    
        #is it an unconditional branch instruction?
        #These have the form goto label
        elif (len(line)==2) and (line[0]=='goto') and allin(line[1],alphanum):
            #print 'unconditional branch'
            label=line[1]
            obj.append('B'+'#'+label)
            current+=1
            
        #is it a decrement instruction?
        #these have the form dec variable
        elif (len(line)==2) and (line[0]=='dec') and (len(line[1])==1) and (line[1][0] in letters):
            #print 'decrement'
            obj.append('D'+line[1][0])
            current+=1
            
        #is is an increment instruction?
        elif (len(line)==2) and (line[0]=='inc') and (len(line[1])==1) and (line[1][0] in letters):
            #print 'increment'
            obj.append('I'+line[1][0])
            current+=1

        #is it a MACRO call?
        elif (len(line)>=3) and (line[0] == 'MACRO'):
            file = line[1]
            if file not in child_programs:
                prog, children = assemble_from_file(file, macro=True)

                # store the child program's children in the global dictionary. this flattens the child tree
                for child_name, child_prog in children.items():
                    if child_name not in child_programs:
                        child_programs[child_name] = child_prog

                child_programs[file] = prog, {}
            obj.append('M'+file+'#'+''.join(line[2:]))
            current+=1
            
        #is it a halt instruction?
        elif (len(line)==1) and (line[0]=='halt'):
            #print 'halt'
            obj.append('H')
            current+=1
    #resolve symbol table references
    for j in range(len(obj)):
        instruction=obj[j]
        if instruction[0]=='B':
            place=instruction.index('#')
            label=instruction[place+1:]
            if not label in symbol_table:
                sys.exit('undefined label '+label)
            else:
                instruction=instruction[:place]+str(symbol_table[label])
                obj[j]=instruction
    return obj, child_programs

#Now produce object code from source file.  Skip comments and blank lines.
def assemble_from_file(filename, macro=False):
    if macro:
        filename += '.cp'
    with open(filename, 'r') as f:
        source=[]
        for line in f:
            if (line[0]!='#') and not allin(line,string.whitespace):
                source.append(line.split())
    #print source
    return assemble(source)

#run a program from a file on a sequence of inputs
def runcp(filename,*args,**kwargs):
    obj = assemble_from_file(filename)
    return interpret(obj,*args,**kwargs)

def is_valid_file(arg):
    if not os.path.isfile(arg):
        if os.path.isfile(arg + '.cp'):
            return arg + '.cp'
        raise argparse.ArgumentTypeError('%s is not a valid file.' % arg)
    return arg

def is_valid_initial(arg):
    try:
        val = int(arg)
        if val < 0:
            raise argparse.ArgumentTypeError('%s is not a positive integer.' % arg)
        return int(arg)
    except:
        raise argparse.ArgumentTypeError('%s is not a positive integer.' % arg)

if __name__ == "__main__":
    import argparse
    import os.path

    parser = argparse.ArgumentParser(description='Assemble and run a counter program.')
    parser.add_argument('file', type=is_valid_file, help='Counter program file name')
    parser.add_argument('initial_values', nargs='+', type=is_valid_initial, help='The initial values for the counter program. These must be positive integers.')
    parser.add_argument('-v', '--verbose',  help='Verbose output', action='store_true')
    parser.add_argument('-vv', '--very-verbose',  help='Extra verbose output', action='store_true')

    args = parser.parse_args()

    print(runcp(args.file, *args.initial_values, verbose=args.verbose, very_verbose=args.very_verbose))
