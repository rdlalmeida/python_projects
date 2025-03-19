import math
import random

def saySomething():
    print("Hello mate, just to confirm this shit is working as supposed!")

# Returns a random number between (2^(n-1)) + 1 and (2^n) - 1
def nBitRandom(n):
    return (random.randrange(2**(n - 1) + 1, (2**n) - 1))

if __name__ == "__main__":
    print("Here are some random primes: ")

    for i in range(105, 110):
        print(nBitRandom(i))
        print("\n")