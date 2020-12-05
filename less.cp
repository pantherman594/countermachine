# check if a < b, storing "1" in c if true and "0" otherwise, without modifying a or b

MACRO cleanup c
MACRO copy a d
MACRO copy b e

loop:
goto reject if e=0
goto accept if d=0
dec d
dec e
goto loop

accept:
inc c
goto finish

reject:
goto finish

finish:
MACRO cleanup d
MACRO cleanup e
halt
