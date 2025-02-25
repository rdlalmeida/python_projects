class ASeries(object):
    def __init__(self):
        self.min_values = 2
        self.max_values = 50

        self.min_val = -1000000
        self.max_val = 1000000

    # Main method
    def longest(self, values):
        aser = ASeries()

        value_list = aser.verify_values(values)

        value_list = sorted(value_list)

        minim = aser.get_min_interval(value_list)

        maxim = aser.get_max_interval(value_list)

        diff_lines = []

        # Using the difference line method the last element yields a line of zeros every time, thus I'm not even bothering with calculate it
        for i in range(0, len(value_list) - 1):
            diff_lines.append(aser.calculate_difference_line(value_list[i], minim, maxim, value_list))

        # Now its easy: with all the difference line already calculated, the value that I'm looking for is just the maximum element in all lines:
        return max(max(diff_lines))

    # Simple method to validate the input's constrains and change the input data set from a set to a list
    def verify_values(self, values):
        if len(values) < self.min_values or len(values) > self.max_values:
            raise Exception("ERROR: invalid input elements.")

        for value in values:
            if value < self.min_val or value > self.max_val:
                raise Exception("ERROR: The input element exceeds its limits.")

        return values

    # Simple method to print a list of values
    def print_list(self, value_list):
        if len(value_list) < self.min_values or len(value_list) > self.max_values:
            raise Exception("ERROR: Invalid number of elements.")

        print("Value list: [", end='')
        for i in range(0, len(value_list) - 1):
            print(str(value_list[i]) + ", ", end='')

        print(str(value_list[-1]) + "]")

    # Simple method to determine the maximum interval between any numbers in a list
    def get_max_interval(self, value_list):

        # Start by sorting the provided list
        value_list = sorted(value_list)

        # For this one simply return the difference between the list extremes
        return int(value_list[-1]) - int(value_list[0])

    # Method to determine the minimum interval between any numbers in a list
    def get_min_interval(self, value_list):

        # Same thing as before: start by sorting the list
        value_list = sorted(value_list)

        minim = value_list[-1]                # Start by assigning the largest element of the list to the minimum value

        # Logically, the minimum difference between any of the elements of the list is necessarily a difference between two consecutive elements on a sorted list. As so:
        for i in range(1, len(value_list)):
            diff = value_list[i] - value_list[i - 1]    # For each pair of consecutive element, calculate their difference.

            # If the operation finds a smaller value than before
            if diff < minim:
                minim = diff      # Update the minimum value

        return minim

    # Method to calculate the difference line for a list element. This line is basically a 1 x n matrix where n = [minim, minim + 1, minim + 2, ..., max] and calculates the number
    # of elements in the list that can be achieved by adding the respective value, i.e, the longest series of elements split by the same quantity
    # Example: for the [3, 8, 4, 5, 6, 2, 2] sequence, minim = 0 (2 - 2) and max = 6 (8 - 2). So for the first element of the list (2), the difference line is:
    #       0   1   2   3   4   5   6
    #   2   1   5   4   3   2   0   1
    #
    # This reads as: if I add "1" to element "2" I can get 5 elements on the list, i.e, I can create a 5 element sequence whose difference is "1" (2, 3, 4, 5 and 6)
    # But adding "2" to "2" I can only get a 4 element sequence: 2, 4, 6 and 8.
    # From here it should be easy to identify the largest sequence possible
    def calculate_difference_line(self, line_header, minim, maxim, value_list):
        if minim > maxim:
            raise Exception("ERROR: Invalid threshold limits")

        if line_header not in value_list:
            raise Exception("ERROR: The difference line header does not belong to the original element list")

        diff_line = []                      # I'm gonna put the results here

        # Go through all elements in the possible limit (specify step = 1 just in case) and since I'm interested in the results for i = maxim, I have to add '1' to range's
        # upper limit because it gets omitted by default
        for i in range(minim, maxim + 1, 1):
            # CAREFUL: If my jump, i.e, my i variable is 0, then I'm gonna get struck in a while loop further down. As such I need to make sure that the i = 0 case is treated
            # as a special one
            if i != 0:
                ref_value = line_header             # Reference value starts as the same as line header but then gets incremented and thus why the new variable
                jump = i                            # How much am I gonna add to the reference value on each iteration
                occurrences = 0                      # Number of elements found in the list

                # Do jumps until falling off the edge of the list
                while ref_value + jump <= value_list[-1]:
                    # If, by adding the jump value, I got an element on the list
                    if (ref_value + jump) in value_list:
                        occurrences = occurrences + 1             # Then add it up
                    else:
                        break

                    ref_value = ref_value + jump                # And then increment the reference value to see if I can get more elements into the sequence

                # I'm off that while above, and so I need to add one more to count to take the original value into account (thrust me, it makes sense...), but only if I found a previous
                # element before, that is, I'm not counting 1 element sequences (because I'm lazy...)
                if occurrences > 0:
                    occurrences = occurrences + 1

                diff_line.append(occurrences)
            else:
                # If my jump is 0, then I'm effectively counting how many copies of line_header exist in value_list. Easy!
                occurrences = value_list.count(line_header)

                if occurrences > 1:
                    diff_line.append(occurrences)
                else:
                    diff_line.append(0)

        return diff_line