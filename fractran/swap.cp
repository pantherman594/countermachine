# swap values at a and b

goto altswap if a=0
loop:
goto finish if a=0
dec a
inc b
goto loop
altswap:
goto finish if b=0
dec b
inc a
goto altswap
finish:
halt