import random

class ABC(object):
    # Main method
    def createString(self, N, K):
        if N < 3 or N > 30:
            raise Exception("ERROR: Invalid input N.")

        if K < 0 or K > N*(N - 1)/2:
            raise Exception("ERROR: Invalid input K.")
        s = ""

        abc = ABC()

        # Before going any further, lets get the maximum K string and see if it is possible to generate a string with the provided K value
        max_s = abc.get_maximum_string(N)
        max_k = abc.get_k(max_s)

        # If it is impossible to generate such string
        if K > max_k:
            return ""
        # If per chance the input K is the maximum one, simply return max_s
        elif K == max_k:
            return max_s
        elif K == 0:
            return abc.get_minimum_string(max_s)
        else:
            # Before anything else, lets resume my options:
            # I have defined 4 zones in the string:
            # Zone 0 = [0, 1/3N]
            # Zone 1 = [1/3N, 1/2N]
            # Zone 2 = [1/2N, 2/3N]
            # Zone 3 = [2/3N, N]

            # Each zone has 6 possible letter swaps that affect K:
            # Swap 1 = B -> A
            # Swap 2 = C -> A
            # Swap 3 = C -> B
            # Swap 4 = A -> B
            # Swap 5 = A -> C
            # Swap 6 = B -> C

            # The ration in which K is affected by these swaps has been thoroughly calculated and the final results can be defined from the following data structures:
            z0 = [0, round(N/3)]
            z1 = [z0[1], round(N/2)]
            z2 = [z1[1], round(2*N/3)]
            z3 = [z2[1], N]

            # And now for all possible letter swaps
            sw1 = ["A", "B"]
            sw2 = ["B", "C"]
            sw3 = ["A", "C"]
            sw4 = ["B", "A"]
            sw5 = ["C", "B"]
            sw6 = ["C", "A"]

            # And finally a map out of all possible combinations by levels of K manipulation
            possible_K = [
                [sw1, z0],
                [sw1, z1],
                [sw1, z2],
                [sw1, z3],
                [sw2, z0],
                [sw2, z1],
                [sw2, z2],
                [sw2, z3],
                [sw3, z0],
                [sw3, z1],
                [sw3, z2],
                [sw3, z3],
                [sw4, z0],
                [sw4, z1],
                [sw4, z2],
                [sw4, z3],
                [sw5, z0],
                [sw5, z1],
                [sw5, z2],
                [sw5, z3],
                [sw6, z0],
                [sw6, z1],
                [sw6, z2],
                [sw6, z3]
            ]

            # With all the possibilities mapped out, I can now develop a simple converging algorithm that will eventually find a string that computes
            # the desired K value
            s = max_s                           # Start with the maximum K possible. I could as easily start with K = 0 and go up from there. Should be the same hopefully
            max_k = abc.get_k(s)

            count = 0

            # This is the main thing right here: until I achieve the desired K I'm going to loop over the same set of instructions
            while abc.get_k(s) != K and count < 100:
                # An extensive but reasonable approach is to, for a given starting string, calculate all possible K changes and decide for the one that gets closer to
                # the desired final K value.

                new_strings = abc.calculate_new_strings(s, possible_K)
                # Calculate the relevant K increases from the string list just obtained
                k_range = []

                for s in new_strings:
                    # For invalid swaps
                    if s == "X":
                        # Pad the result with a "0"
                        k_range.append(0)
                    else:
                        # Otherwise calculate the relevant K value
                        k_range.append(abc.get_k(s))

                    # From here calculate which of the swap pairs has achieved a closer value for K
                optimum_index = abc.find_optimum_index(K, k_range)

                    # And update the string to reflect that
                s = new_strings[optimum_index]

#                print ("Count = " + str(count))
#                print ("k_range = ", end='')
#                print (k_range)
#                print ("Optimum index = " + str(optimum_index))
#                print ("New s = " + s, end='')
#                print (" K = " + str(abc.get_k(s)))
                count = count + 1
            print ("Loops until result: " + str(count))
        return s

    # This method simply receives a desired K value and the list with all the computations of K and returns the index of the swap that generated the closest K to the target
    def find_optimum_index(self, K, k_range):
        if len(k_range) != 24:
            raise Exception("ERROR: Invalid lenght for the K results array.")

        # Calculate the difference between the first result and the target K
        min_diff_K = -1
        optimum_index = -1

        for i in range (0, len(k_range)):
            # I have to protect myself against "0" in k_range because those denote impossible swaps, i.e, swaps that result on s = "X"
            if k_range[i] == 0 and K != 0:
                continue
            # Check if there any results closer to target K
            # If that's so

            if K in k_range:
                return k_range.index(K)

            if abs(K - k_range[i]) < min_diff_K or min_diff_K == -1:
                # Update the index
                optimum_index = i
                # And the minimum difference
                min_diff_K = abs(K - k_range[i])

        if min_diff_K == -1 and optimum_index == -1:
            raise Exception("ERROR: The k_range array has only zeros on in!")
        return optimum_index


    # This method receives a string and a combination of swaps and zones and calculates all possible string modifications by applying each one of the possible
    # swaps to the current string, i.e, I'm analysing just one single change at a time
    def calculate_new_strings(self, s, combo_list):
        if len(combo_list) < 0 or len(combo_list) > 24:
            raise Exception("ERROR: Invalid combo list: " + combo_list)

        new_strings = []                                # I'm putting my calculations of K right here
        abc = ABC()                                 # Same old class instantiation

        for combo in combo_list:
            if len(combo[0]) != 2 or len(combo[1]) != 2:
                raise Exception("ERROR: Invalid combo elements (length != 2)")
            # Calculate new K for each possible combination
            new_s = abc.manipulate_K(s, combo[0], combo[1])

            # Now I'm going to simply put all the possible string combinations in the result list and return it
            new_strings.append(new_s)

        # Return the list of results when done
        return new_strings


    # Here I want to rewrite the past 24 functions in a way where I only need to call one single function with all parameter combinations already mapped out
    # in data structures
    def manipulate_K(self, s, letters_to_swap, zone):
        abc = ABC()

        abc.validate_zone(s, zone)
        s = abc.replace_letters(s, letters_to_swap[0], letters_to_swap[1], zone[0], zone[1])

        return s

    # Method to validate an input zone (very similar to the limits approach)
    def validate_zone(self, s, zone):
        if len(zone) != 2:
            raise Exception("ERROR: Invalid zone element.")

        if not 0 <= zone[0] <= zone[1] <= len(s):
            raise Exception("ERROR: Invalid zone thresholds.")

    # Simple method to printout the zone limits
    def print_zones(self, z0, z1, z2, z3):
        print("Z0 = [" + str(z0[0]) + ", " + str(z0[1]) + "]")
        print("Z1 = [" + str(z1[0]) + ", " + str(z1[1]) + "]")
        print("Z2 = [" + str(z2[0]) + ", " + str(z2[1]) + "]")
        print("Z3 = [" + str(z3[0]) + ", " + str(z3[1]) + "]")

    # Method to calculate K extensively, that is, by "manually" counting each valid pair (AB, AC and BC in the string). There might be an algebraic method to calculate K but
    # this one does it extensively and as such I'm assuming that it is valid
    def get_k(self, s):
        abc = ABC()

        # Validate the input string plus convert it to upper case
        s = abc.validate_string(s)

        k = 0                   # Initiate the counter

        for i in range(0, len(s)):
            # For this case I don't need to count any combinations started with "C" (there aren't any) and I don't need to check the last element of the sequence (s[len(s) - 1] because
            # there are no sequences that I can construct from that point onwards
            if s[i] != "C" and i < len(s) - 1:
                # So, if I get an "A" or a "B", check the rest of the sequence
                for j in range(i + 1, len(s)):
                    # Add "1" to "k" anytime that I get an "AB", "AC" or "BC"
                    if (s[i] == "A" and s[j] in ["B", "C"]) or (s[i] == "B" and s[j] == "C"):
                        k = k + 1

        return k

    # Simple method to validate a string, that is, check if all its elements are only "A", "B" or "C". Also, just for kicks, I'm converting the string to upper case just in case
    def validate_string(self,s):
        s = s.upper()

        for letter in s:
            if letter not in ["A", "B", "C"]:
                raise Exception("ERROR: Invalid input string")

        return s

    # Method that generates a string that yields the maximum possible K value for a given N. This value results from a even and ordered distribution of A, B and C's. Example,
    # for N = 6, the maximum K is achieved with the string "AABBCC" (K = 12). Any deviation from this sequence (since 6 is a multiple of 3 in this case) yields a smaller K
    # This results were obtained numerically, i.e, through exhausting experimentation. Ideally I should come up with a mathematical proof of the thing at some point. For N values
    # not multiple of 3 it seems that as long as the 1/3 rule is respected to an extent, the sequence yields the largest K possible. For instance, if N = 8, a possible max_K string
    # can be "AAABBBCC" (K = 21). As long as the difference between any number of characters doesn't exceed "1", that is, as long as mod(count(A)) - mod(count(B)) <= mod(count(A))
    # - mod(count(C)) <= mod(count(B)) - mod(count(C)) <= 1, I always get a maximum K.
    # K(AAABBBCC) = K(AAABBCCC) = K(AABBBCCC) = 21
    def get_maximum_string(self, N):
        number_A = round(N/3)                       # Number of "A"s
        number_B = number_A                         # Number of "B"s
        number_C = N - number_A - number_B

        s = ""

        for i in range(0, N):
            if i < number_A:
                s = s + "A"
            elif i < number_A + number_B:
                s = s + "B"
            else:
                s = s + "C"

        return s

    # Similar method to the one above but this one to generate the minimum string, which incidentally is the inverse of the maximum string...literally
    def get_minimum_string(self, max_s):
        minimum_s = []

        for i in range (len(max_s) - 1, -1, -1):
            minimum_s.append(max_s[i])

        return "".join(minimum_s)


    # Next I'm going to write methods very similar between them that perform big and small increases and decreases in K. Small increases are going to happen when I swap
    # consecutive letters around in specific areas of the string. For example, changing a "C" to a "B" in the first or middle thirds or a "B" to an "A" in the upper third.
    # A large increase occurs when non-consecutive letters are swapped in either the upper or lower third of the string, that is, changing a "C" to an "A" in the upper third or
    # an "A" to a "C" in the lower third of the string
    # First one does small increases in K by changing a top "B" into an "A" in the upper half

    ################ UPPER THIRD OF STRING ###########################
    def k_small_increase_up_BA(self, s, limits):

        abc = ABC()

        # Validate the inputs
        abc.validate_limits(s, limits)

        s = abc.replace_letters(s, "B", "A", 0, limits[0])
        return s

    # At the same point I can also change a "C" to a "B" and get a similar small increase in "K"
    def k_small_increase_up_CB(self, s, limits):
        abc = ABC()
        abc.validate_limits(s, limits)

        s = abc.replace_letters(s, "C", "B", 0, limits[0])
        return s

    # Now lets write the inverse function, that is, the one the theoretically should decrease K in the same proportion when applied to the same limits but with inverse letters
    def k_small_decrease_up_AB(self, s, limits):
        abc = ABC()
        abc.validate_limits(s, limits)

        s = abc.replace_letters(s, "A", "B", 0, limits[0])
        return s

    # Same thing but for the other combination
    def k_small_decrease_up_BC(self, s, limits):
        abc = ABC()
        abc.validate_limits(s, limits)

        s = abc.replace_letters(s, "B", "C", 0, limits[0])
        return s

    # Since I'm at it, lets deal with the large increases in K, which happen when non consecutive letters are swapped in the string's extremes
    def k_large_increase_up_CA(self, s, limits):
        abc = ABC()
        abc.validate_limits(s, limits)

        s = abc.replace_letters(s, "C", "A", 0, limits[0])
        return s

    # Same logic inverted for a large decrease in K
    def k_large_decrease_up_AC(self, s, limits):
        abc = ABC()
        abc.validate_limits(s, limits)

        s = abc.replace_letters(s, "A", "C", 0, limits[0])
        return s

    ################ LOWER THIRD OF STRING ###########################
    # The previous 6 functions can easily be rewritten for increases and decreases in K but for the lower third of the string now
    def k_small_increase_low_AB(self, s, limits):

        abc = ABC()

        # Validate the inputs
        abc.validate_limits(s, limits)

        s = abc.replace_letters(s, "A", "B", limits[1], limits[2])
        return s

        # At the same point I can also change a "C" to a "B" and get a similar small increase in "K"

    def k_small_increase_low_BC(self, s, limits):
        abc = ABC()
        abc.validate_limits(s, limits)

        s = abc.replace_letters(s, "B", "C", limits[1], limits[2])
        return s

    # Now lets write the inverse function, that is, the one the theoretically should decrease K in the same proportion when applied to the same limits but with inverse letters
    def k_small_decrease_low_BA(self, s, limits):
        abc = ABC()
        abc.validate_limits(s, limits)

        s = abc.replace_letters(s, "B", "A", limits[1], limits[2])
        return s

        # Same thing but for the other combination

    def k_small_decrease_low_CB(self, s, limits):
        abc = ABC()
        abc.validate_limits(s, limits)

        s = abc.replace_letters(s, "C", "B", limits[1], limits[2])
        return s

    # Since I'm at it, lets deal with the large increases in K, which happen when non consecutive letters are swapped in the string's extremes
    def k_large_increase_low_AC(self, s, limits):
        abc = ABC()
        abc.validate_limits(s, limits)

        s = abc.replace_letters(s, "A", "C", limits[1], limits[2])
        return s

    # Same logic inverted for a large decrease in K
    def k_large_decrease_up_CA(self, s, limits):
        abc = ABC()
        abc.validate_limits(s, limits)

        s = abc.replace_letters(s, "C", "A", limits[1], limits[2])
        return s

    ################ MIDDLE THIRD OF STRING ###########################
    # This one is a bit tricky since changes in the middle section of the string don't yield direct results. It all depends a lot in the state of the string. While changing a "B"
    # to an "A" in the top third of the string or a "B" to a "C" in the lower third gives out an increase in K on pretty much any occasion, the same manipulation in the middle of the
    # string can originate unforeseen increases or decreases. I'm going to leave this functions written just in case but their usage should be done with care.
    # As such I'm going to consider two different zones for this middle area:
    # Zone 1 between 1/3N (limits[0]) and 1/2N. (round(limits[1]/2)
    # Zone 2 is between 1/2N (round(limits[1]/2) + 1) and 2/3N. (limits[1])
    # The increase and decrease rules are as follows:
    # Zone 1: B->A, C->A, C->B = Small increase of K
    # Zone 1: A->B, A->C, B->C = Small decrease of K
    # Zone 2: B->A, C->A, C->B = Small decrease of K
    # Zone 2: A->B, A->C, B->C = Small increase of K

    ############### ZONE 1 #############################################################
    def k_small_increase_middle_BA(self, s, limits):
        abc = ABC()

        abc.validate_limits(s, limits)
        s = abc.replace_letters(s, "B", "A", limits[0], limits[0] + round(limits[1]/2))
        return s

    def k_small_increase_middle_CA(self, s, limits):
        abc = ABC()

        abc.validate_limits(s, limits)
        s = abc.replace_letters(s, "C", "A", limits[0], limits[0] + round(limits[1]/2))
        return s

    def k_small_increase_middle_CB(self, s, limits):
        abc = ABC()

        abc.validate_limits(s, limits)
        s = abc.replace_letters(s, "C", "B", limits[0], limits[0] + round(limits[1]/2))
        return s

    def k_small_decrease_middle_AB(self, s, limits):
        abc = ABC()

        abc.validate_limits(s, limits)
        s = abc.replace_letters(s, "A", "B", limits[0], limits[0] + round(limits[1] / 2))
        return s

    def k_small_decrease_middle_AC(self, s, limits):
        abc = ABC()

        abc.validate_limits(s, limits)
        s = abc.replace_letters(s, "A", "C", limits[0], limits[0] + round(limits[1] / 2))
        return s

    def k_small_decrease_middle_BC(self, s, limits):
        abc = ABC()

        abc.validate_limits(s, limits)
        s = abc.replace_letters(s, "B", "C", limits[0], limits[0] + round(limits[1] / 2))
        return s

    ############### ZONE 2 #############################################################
    def k_small_decrease_middle_BA(self, s, limits):
        abc = ABC()

        abc.validate_limits(s, limits)
        s = abc.replace_letters(s, "B", "A", limits[0] + round(limits[1]/2) + 1, limits[1])
        return s

    def k_small_decrease_middle_CA(self, s, limits):
        abc = ABC()

        abc.validate_limits(s, limits)
        s = abc.replace_letters(s, "C", "A", limits[0] + round(limits[1]/2) + 1, limits[1])
        return s

    def k_small_decrease_middle_CB(self, s, limits):
        abc = ABC()

        abc.validate_limits(s, limits)
        s = abc.replace_letters(s, "C", "B", limits[0] + round(limits[1]/2) + 1, limits[1])
        return s

    def k_small_increase_middle_AB(self, s, limits):
        abc = ABC()

        abc.validate_limits(s, limits)
        s = abc.replace_letters(s, "A", "B", limits[0] + round(limits[1]/2) + 1, limits[1])
        return s

    def k_small_increase_middle_CA(self, s, limits):
        abc = ABC()

        abc.validate_limits(s, limits)
        s = abc.replace_letters(s, "C", "A", limits[0] + round(limits[1]/2) + 1, limits[1])
        return s

    def k_small_increase_middle_CB(self, s, limits):
        abc = ABC()

        abc.validate_limits(s, limits)
        s = abc.replace_letters(s, "C", "B", limits[0] + round(limits[1]/2) + 1, limits[1])
        return s

    #################################### END OF K MANIPULATION FUNCTIONS ###################################



    # Simple method to validate the input made as zone limits
    def validate_limits(self, s, limits):
        if len(limits) != 3:
            raise Exception("ERROR: Invalid limit element.")

        if not (limits[0] < limits[1] < limits[2]):
            raise Exception("ERROR: Invalid zone thresholds.")

        if len(s) != limits[2]:
            raise Exception("ERROR: The string provided doesn't match its limits.")

    # Simple method that receives a origin_letter and a destin_letter and checks and replaces (if possible) the origin_letter by the destin_letter for the interval supplied
    def replace_letters(self, s, origin_letter, destin_letter, lower_limit, higher_limit):
        # Input validation, as always
        if not origin_letter.upper() in ["A", "B", "C"]:
            raise Exception("ERROR: Invalid origin letter: " + str(origin_letter))
        elif not destin_letter.upper() in ["A", "B", "C"]:
            raise Exception("ERROR: Invalid destination letter: " + str(destin_letter))
        elif not lower_limit <= higher_limit <= len(s):
            raise Exception("ERROR: Invalid input limits: " + str(lower_limit) + " and " + str(higher_limit))

        # Begin by checking if the origin letter is in the section of the string in question
        if origin_letter in s[lower_limit:higher_limit - 1]:
            # If so, start by getting an index value somewhere inside the limit
            index = random.randint(lower_limit, higher_limit - 1)

            # Circle the limit until finding the letter that I'm looking for
            while s[index] != origin_letter:
                # Increment the index on each interaction
                index = index + 1
                # And if I step out of bounds
                if index >= higher_limit:
                    # Reset the index to the beginning of the limit
                    index = lower_limit

            # And now the python process to replace a single character in a string
            s_list = list(s)
            s_list[index] = destin_letter
            s = "".join(s_list)

            return s                            # And return the modified string

        # If I couldn't find a origin letter in the limit provided, return a specific character to deal with the consequences latter
        else:
            return "X"
