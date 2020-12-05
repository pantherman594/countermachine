# simply adds a and b, returns output to a

loop:
goto finish if b=0
dec b
inc a
goto loop
finish:
halt