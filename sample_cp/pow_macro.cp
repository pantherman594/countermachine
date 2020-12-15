# use macro compute a^b

MACRO swap a c
inc a

loop:
goto finish if b=0
MACRO copy c d
MACRO mult_macro a d
dec b
goto loop

finish:
MACRO cleanup c
MACRO cleanup d
halt
