# use macro multiply a and b

MACRO swap a c

loop:
goto finish if b = 0
MACRO copy c d e
MACRO add a d
dec b
goto loop

finish:
MACRO cleanup c
MACRO cleanup d
halt
