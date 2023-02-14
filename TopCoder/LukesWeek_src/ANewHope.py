class ANewHope(object):
    # Main method
    def count(self, first_week, last_week, d):
        # Check input args for constrains
        if len(first_week) < 2 or len(first_week) > 2500 or len(first_week) != len(last_week):
            raise Exception("ERROR: Invalid input parameters.")

        # Get the number of days in that week
        N = len(first_week)

        # Check one more constrain
        if d < 1 or d > (N + 1):
            raise Exception("ERROR: Invalid value for 'D'")

        week_count = 1                                      # Main week counter

        nh = ANewHope()

        # At this point I'm assuming first_week != last_week so I can do at least one wash cycle in my code
        # Start by creating an array of Shirts
        current_week = nh.prepare_shirts(first_week)

        # Do the following while the current and last week arrays don't match
        while not nh.is_current_week_last(current_week, last_week):
            # Week's done. Lets do some laundry
            laundry_basket = nh.go_through_week(current_week, d)
            week_count = week_count + 1  # Put at least one week in the counter

            current_week = nh.plan_new_week(laundry_basket, last_week)

            print("Week #" + str(week_count))

            for shirt in current_week:
                print(str(shirt.get_name()))

            print()

        return week_count

    class Shirt:
        """Simple object representing one of Luke's shirts"""

        def __init__(self, name, wash_count):
            self.name = name
            self.wash_count = wash_count

        def get_name(self):
            return self.name

        def get_wash_count(self):
            return self.wash_count

    # Simple method to convert an integer array into a array of shirts
    def prepare_shirts(self, first_week):
        week_wardrobe = []

        nh = ANewHope()

        for i in range(0, len(first_week)):
            temp_shirt = nh.Shirt(str(first_week[i]), 0)     # Create a temporary shirt for each array element with a 0 wash count
            week_wardrobe.append(temp_shirt)

        return week_wardrobe

    # Simple method to print a Shirt object
    def print_shirt(shirt):
        print("Shirt name: " + str(shirt.get_name()))
        print("Wash count: " + str(shirt.get_wash_count()) + "\n")

    # Method to simulate the drying process of a shirt that got washed. Runs each day and removes one wash count in order for
    # a shirt to be reused.
    def dry_washed_shirts(self, laundry_basket):
        if len(laundry_basket) == 0:
            return laundry_basket

        for i in range(0, len(laundry_basket)):
            if laundry_basket[i].get_wash_count() > 0:
                laundry_basket[i].wash_count = laundry_basket[i].wash_count - 1

        return laundry_basket

    # This method simulates a running week in which Luke uses all the shirts in its pool for one day and then washes them
    def go_through_week(self, current_week_wardrobe, D):
        laundry_basket = []                     # I'm going to store all dirty and washed shirts in this basket
        nh = ANewHope()
        for day in range(0, len(current_week_wardrobe)):
            # Each iteration on this for loop simulates a day
            laundry_basket = nh.dry_washed_shirts(laundry_basket)      # Start by giving a drying cycle to all shirts in the basket so far

            # Then consider the day done and wash the shirt that Luke is currently wearing
            current_week_wardrobe[day].wash_count = D

            # And add the shirt to the laundry basket
            laundry_basket.append(current_week_wardrobe[day])

        # At the end of the week, return the laundry basket with wet and dry shirts for the next week
        return laundry_basket

    # And now a method to, given a specific laundry basket, plans a new week of shirt wearing while trying to get to last_week arrangement
    def plan_new_week(self, laundry_basket, last_week):
        nh = ANewHope()

        # Its the beginning of day 0 of another week. As such do another drying cycle in the laundry_basket
        laundry_basket = nh.dry_washed_shirts(laundry_basket)

        next_week_shirts = []

        # Now to get the next shirt. The algorithm is quite simple: go for the first shirt on the last week configuration. See if it has a wash count of zero (is available).
        # If not, go for the next shirt in line until one shirt is selected (its guaranteed that at least one shirt with wash count = 0 exists. When that happens, run the dry cycle again
        # and repeat the process until all shirts are selected.
        while len(laundry_basket) > 0:
            # Get the first shirt out of the laundry basket
            index = 0
            temp_shirt = nh.get_shirt_from_name(last_week[index], laundry_basket)

            # Repeat this process until getting a valid shirt out of the laundry basket
            while not temp_shirt or temp_shirt.get_wash_count() > 0:

                index = index + 1                   # Increment the index

                if index > len(last_week):
                    raise Exception("ERROR: Somehow we are looking for more shirts than the ones in the pool.")

                temp_shirt = nh.get_shirt_from_name(last_week[index], laundry_basket)

            next_week_shirts.append(temp_shirt)                 # Add the first valid shirt found to next week's list
            laundry_basket.remove(temp_shirt)                   # And also remove the used shirt from the laundry basket

            # Since I got a shirt for day #0 already, lets dry the whole thing for another day and give it another go
            laundry_basket = nh.dry_washed_shirts(laundry_basket)

        # When all is said and done, I should have the closest sequence possible to last_week in my next_week_shirts array. Return it then
        return next_week_shirts

    # Simple method to retrieve a shirt using its name (number)
    def get_shirt_from_name(self, shirt_name, laundry_basket):
        for shirt in laundry_basket:
            if int(shirt.get_name()) == shirt_name:
                return shirt

        # If I got to this point it means that the required shirt is not in the laundry basket anymore (probably already assigned to a new week)
        return False

    # Method to discern if the current week plan (in shirts) is the desired last_week array (of integers)
    def is_current_week_last(self, current_week, last_week):
        if len(current_week) != len(last_week):
            raise Exception("ERROR: Invalid input arguments.")

        # Check both arrays and return False if an discrepancies are detected
        for i in range(0, len(last_week)):
            if int(current_week[i].get_name()) != int(last_week[i]):
                return False

        return True