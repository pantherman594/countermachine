import math
import string
import sys

digits = '0123456789'
fractran_allowed = digits + '*'

def allin(s,charset):
    for c in s:
        if not (c in charset):
            return False
    return True

# Derived from https://stackoverflow.com/a/16996439
def prime_factorize(n):
    if n < 2:
        return [[-1, 0]]

    primes = []
    candidate = 2

    while candidate * candidate <= n:
        count = 0

        while (n % candidate) == 0:
            count += 1
            n = n // candidate

        if count > 0:
            primes.append([candidate, count])

        candidate += 1

    if n > 1:
        primes.append([n, 1])

    return primes

# Sieve of Eratosthenes
# Code by David Eppstein, UC Irvine, 28 Feb 2002
# http://code.activestate.com/recipes/117119/

def gen_primes():
    """ Generate an infinite sequence of prime numbers.
    """
    # Maps composites to primes witnessing their compositeness.
    # This is memory efficient, as the sieve is not "run forward"
    # indefinitely, but only as long as required by the current
    # number being tested.
    #
    D = {}

    # The running integer that's checked for primeness
    q = 2

    while True:
        if q not in D:
            # q is a new prime.
            # Yield it and mark its first multiple that isn't
            # already marked in previous iterations
            # 
            yield q
            D[q * q] = [q]
        else:
            # q is composite. D[q] is the list of primes that
            # divide it. Since we've reached q, we no longer
            # need it in the map, but we'll mark the next 
            # multiples of its witnesses to prepare for larger
            # numbers
            # 
            for p in D[q]:
                D.setdefault(p + q, []).append(p)
            del D[q]

        q += 1

# Calculate the GCD of a and b using the Euclidian algorithm.
def gcd(a, b):
    while b:
        a, b = b, a % b
    return a

# A source program is here represented as a sequence of lines, each
# line a list of strings. Transpile the machine into a counter program,
# and return its lines. This uses the less and cleanup macros. Counters
# y and z will be reserved for checking less than.

def transpile(source):
    # Convert the lines into their prime factors
    fractions = []

    for line_num, line in enumerate(source):
        if len(line) != 2 or not (allin(line[0] + line[1], fractran_allowed)):
            sys.exit('Invalid line on {}: {}'.format(line_num + 1, ' '.join(line)))

        try:
            # eval the expression to allow for the format a*b
            line_int = [int(eval(x)) for x in line]

            for x in line_int:
                if x < 1:
                    sys.exit('Invalid line on {}: {}'.format(line_num + 1, ' '.join(line)))

            # Compute the GCD to simplify the fraction
            nd_gcd = gcd(*line_int)

            fractions.append([prime_factorize(x/nd_gcd) for x in line_int])
        except:
            sys.exit('Invalid line on {}: {}'.format(line_num + 1, ' '.join(line)))

    # Find the largest prime in the series, then find all the primes up to and including that.
    max_prime = 0

    for parts in fractions:
        for part in parts:
            if part[-1][0] > max_prime:
                max_prime = part[-1][0]

    primes = {}
    primes[-1] = -1
    for i, prime in enumerate(gen_primes()):
        if prime > max_prime:
            break

        primes[prime] = i

    # Convert prime numbers into counter numbers
    for parts in fractions:
        for i in range(len(parts)):
            parts[i] = [[primes[prime], count] for prime, count in parts[i]]

    # Convert to counter program
    if primes[max_prime] > 24:
        sys.exit('This FRACTRAN program uses more counters than we have.')

    counter_program = []
    label = 0

    for numerator, denominator in fractions:
        counter_program.append(['step_{}:'.format(label)])
        label += 1

        for counter, count in denominator:
            if counter == -1:
                break

            # set y to count - 1
            counter_program.append(['MACRO', 'cleanup', 'y'])
            for i in range(count - 1):
                counter_program.append(['inc', 'y'])

            # jump to next step if counter is less than count (here, written as:
            # if count - 1 is not less than counter)
            counter_program.append(['MACRO', 'less', 'y', chr(ord('a') + counter), 'z'])
            counter_program.append(['goto', 'step_{}'.format(label), 'if', 'z=0'])

        for counter, count in numerator:
            if counter == -1:
                break

            for i in range(count):
                counter_program.append(['inc', chr(ord('a') + counter)])


        for counter, count in denominator:
            if counter == -1:
                break

            for i in range(count):
                counter_program.append(['dec', chr(ord('a') + counter)])

        counter_program.append(['goto', 'step_0'])

    counter_program.append(['step_{}:'.format(label)])
    counter_program.append(['MACRO', 'cleanup', 'y'])
    counter_program.append(['MACRO', 'cleanup', 'z'])
    counter_program.append(['halt'])

    return counter_program

def transpile_from_file(filename, output):
    with open(filename, 'r') as f:
        source=[]
        for line in f:
            if (line[0]!='#') and not allin(line,string.whitespace):
                source.append(line.split())

    cp = transpile(source)

    with open(output, 'w') as f:
        for line in cp:
            f.write(' '.join(line) + '\n')

def is_valid_file(arg):
    if not os.path.isfile(arg):
        if os.path.isfile(arg + '.cp'):
            return arg + '.cp'
        raise argparse.ArgumentTypeError('%s is not a valid file.' % arg)
    return arg

if __name__ == "__main__":
    import argparse
    import os

    parser = argparse.ArgumentParser(description='Transpile a FRACTRAN program into a counter machine program')
    parser.add_argument('input', type=is_valid_file, help='FRACTRAN program file name')
    parser.add_argument('output', help='Counter machine program file name')

    args = parser.parse_args()

    transpile_from_file(args.input, args.output)
    print('Output written to', args.output)
