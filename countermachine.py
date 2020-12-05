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


def interpret(program,*args,**kwargs):
    counters=[0]*26
    for j in range(len(args)):
        counters[j]=args[j]
    if 'verbose' in kwargs:
        verbose=kwargs['verbose']
    else:
        verbose=False
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
            
    return counters

######################################################

# changing the references to counters in program, to match those of counters, and append those to obj

def integrate(program,counters, obj, current):

    # create a new variable to keep track of current since we need the original current to offset goto calls
    final_current = current

    for line in program:
        # create the new translated line beginning with the first character (is typically H, I, D, or B)
        newline = ''+line[0]

        # for I and D, simply translate the counter values and concatenate it with newline
        if line[0] == 'I' or line[0] == 'D':
            found_var = False
            for i in range(len(counters)):
                if (ord('a')+i) == ord(line[1]):
                    newline += counters[i][0]
                    found_var = True
            if not found_var:
                sys.exit('MACRO: counter assignment not found')

        # for B with conditions, we convert both counter value and the goto line
        elif line[0] == 'B' and (line[1] in letters):
            found_var = False
            for i in range(len(counters)):
                if (ord('a')+i) == ord(line[1]):
                    newline += counters[i][0]
                    found_var = True
            if not found_var:
                sys.exit('MACRO: counter assignment not found')
            newline+=str(int(line[2:])+current)

        # for unconditional B, we simply convert the goto line
        elif line[0] == 'B':
            newline += str(int(line[1:])+current)
        obj.append(newline)
        final_current+=1

    # we check our converted code for any H, and change those to goto whatever comes after our translated code
    for index in range(len(obj)):
        if obj[index] == 'H':
            newline='B'
            newline+=str(final_current)
            obj[index] = newline
    return obj, final_current

######################################################


#A source program is here represented as a sequence of lines, each
#line a list of strings.  Assemble the source program into the lower-level
#code used above, and return the low-level program.

def assemble(source):
    symbol_table={}
    obj=[]
    already_assembled=[]
    current=0
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
            
        #is it a halt instruction?
        elif (len(line)==1) and (line[0]=='halt'):
            #print 'halt'
            obj.append('H')
            current+=1

#############################################
            
        #is it a MACRO call?
        elif (len(line)>=3) and (line[0] == 'MACRO'):
            #we would essentially insert the counter machine code from the macro call into the assembled language.
            pair = [0]*2
            pair[0] = current
            obj, current = integrate(assemble_from_file(line[1],macro=True), line[2:], obj, current)
            pair[1] = current
            already_assembled.append(pair)
            
############################################# modifications also made to below code where we resolve table references
            
    #resolve symbol table references
    for j in range(len(obj)):
        instruction=obj[j]
        if instruction[0]=='B':
            # if j is not in the range of any of the pairs of already_assembled, then we do below code
            not_yet_assembled = True
            for pair in already_assembled:
                for checking in range(pair[0],pair[1]):
                    if j == checking:
                        not_yet_assembled = False
                        
            if not_yet_assembled:
                place=instruction.index('#')
                label=instruction[place+1:]
                if not label in symbol_table:
                    sys.exit('undefined label '+label)
                else:
                    instruction=instruction[:place]+str(symbol_table[label])
                    obj[j]=instruction
    return obj

#Now produce object code from source file.  Skip comments and blank lines.
def assemble_from_file(filename,macro=False):
    # if this is assembled as a macro call, then we need to append '.cp' to find the file
    if macro:
        filename+='.cp'
    f=open(filename,'r')
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
            
    
            

    
