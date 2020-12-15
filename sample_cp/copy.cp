# Write a counter machine program that starts with a value x in counter
# a (with all other counters assumed to be zero) and finishes with the value x
# in counters a and b. This trick for ‘copying’ values will be useful in solving
# some of the other problems.

loop:
goto finish if a=0
dec a
inc b
inc c
goto loop

finish:
MACRO swap a c
halt