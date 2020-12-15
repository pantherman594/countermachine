# multiplies a and b by adding a to itself b times

# return 1 if b=0
goto return_one if b=0
dec b

# just return the value of a if b=0
goto finish if b=0

# move b to f
setup:
goto setup2 if b=0
dec b
inc f
goto setup

# move a to b and c
setup2:
goto multsetup if a=0
dec a
inc b
inc c
goto setup2

multsetup:
print
goto finish if f=0
dec f
multsetuploop:
goto copy if a=0
dec a
inc b
goto multsetuploop

# copy c to d and e, decrementing b
copy:
print
goto multsetup if b=0
dec b
copyloop:
goto move if c=0
dec c
inc d
inc e
goto copyloop

# move e to c
move:
goto add if e=0
dec e
inc c
goto move

# add d to a
add:
goto copy if d=0
dec d
inc a
goto add

# set a to 1 and quit
return_one:
clear_a:
goto set_a if a=0
dec a
goto clear_a
set_a:
inc a
goto finish

finish:
halt
