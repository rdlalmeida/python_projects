import sys
import random

def saySomething():
    print("Hello mate, just to confirm this shit is working as supposed!")


# Returns a random number between (2^(n-1)) + 1 and (2^n) - 1
def nBitRandom(n):
    return (random.randrange(2**(n - 1) + 1, (2**n) - 1))


def SieveOfEratosthenes(n):
    '''Generates all first primes up to the argument p and returns it as list'''
    # By some stupid reason, python insists in treating n as string! 
    # I need to force cast it to int for this to work
    n = int(n)

    # Create a boolean array "prime [0..n]" and initialize all entries as true.
    # A value is prime[i] will finally be false if i is not a prime, else is true
    prime = [True] * (n + 1)
    p = 2

    while (p * p <= n):
        # If prime[p] is not changed, then it is a prime
        if (prime[p] == True):

            # Update all multiples of p
            for i in range(p * p, n + 1, p):
                prime[i] = False

        p += 1

    prime_list = []
    # Send the indexes of True elements to the prime_list
    for p in range(2, n + 1):
        if (prime[p]):
            prime_list.append(p)

    # Done. Return it
    return prime_list


def getLowLevelPrime(n):
    '''Generate a prime candidate divisible by first primes'''
    # Same as before. Python gets arguments as strings for default
    n = int(n)

    first_primes_list = SieveOfEratosthenes(n)

    # Repeat until a number satisfying the test isn't found
    while True:
        # Get a random number
        prime_candidate = nBitRandom(n)

        for divisor in first_primes_list:
            if prime_candidate % divisor == 0 and divisor**2 <= prime_candidate:
                break

            # If no divisor found, return value
            else: return prime_candidate


def isMillerRabinPassed(mrc):
    '''Run 20 iterations of the Rabin Miller Primality test'''
    mrc = int(mrc)
    
    maxDivisionsByTwo = 0
    ec = mrc - 1

    while ec % 2 == 0:
        ec >>= 1
        maxDivisionsByTwo += 1

    assert(2**maxDivisionsByTwo * ec == mrc - 1)

    def trialComposite(round_tester):
        if pow(round_tester, ec, mrc) == 1:
            return False

        for i in range(maxDivisionsByTwo):
            if pow(round_tester, 2**i * ec, mrc) == mrc - 1:
                return False
        
        return True

    # Set number of trials here
    numberOfRabinTrials = 20

    for i in range(numberOfRabinTrials):
        round_tester = random.randrange(2, mrc)

        if trialComposite(round_tester):
            return False
    
    return True

def getLargePrime(n):
    '''
        This function encapsulates all the logic required to obtain a large and valid prime number.
        It receives an upper limit bound in n, and essentially generates pseudo-primes randomly using
        the getLowerLevelPrime and run 20 rounds of the Rabin Miller algorithm to return a large prime
        with high probability. The idea is that only primes can survive 20 rounds of this algorithm
    '''
    n = int(n)

    while True:
        prime_candidate = getLowLevelPrime(n)

        if not isMillerRabinPassed(prime_candidate):
            continue
        else:
            return prime_candidate
    

if __name__ == "__main__":
    n = sys.argv[1]
    # print("Here are all the primes from 0 to " + str(n) + ": ")

    # prime_list = SieveOfEratosthenes(n)

    # for i in prime_list:
    #     print(str(i) + " ", sep="")

    print("Low Lever prime for n = " + str(n) + ":")
    print(getLargePrime(n))