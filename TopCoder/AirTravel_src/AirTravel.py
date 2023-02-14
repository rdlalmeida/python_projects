import math

class AirTravel(object):
    # Main method
    def shortestTrip(self, latitude, longitude, canTravel, origin, destination):
        # Lets validate all the inputs at this point
        if len(latitude) != len(longitude) != len(canTravel):
            raise Exception("ERROR: The latitude, longitude and canTravel lists have different sizes among them!")

        # Validate latitudes
        if not isinstance(latitude, list):
            raise Exception("ERROR: The latitude input is not a list! (Its actually a " + str(type(latitude)) + ")")
        if len(latitude) < 1 or len(latitude) > 20:
            raise Exception("ERROR: Wrong number of latitude elements (min = 1, max = 20): " + str(len(latitude)))

        for lat in latitude:
            if not isinstance(lat, int):
                raise Exception("ERROR: There's a non integer element in the latitude list: " + str(lat) + " is a " + str(type(lat)))
            if lat < -90 or lat > 90:
                raise Exception("ERROR: Invalid latitude value (min = -89, max = 89): " + str(lat))

        # Validate longitudes
        if not isinstance(longitude, list):
            raise Exception("ERROR: The longitude input is not a list! (Its actually a " + str(type(longitude)) + ")")
        if len(longitude) < 1 or len(longitude) > 20:
            raise Exception("ERROR: Wrong number of longitude elements (min = 1, max = 20): " + str(len(longitude)))
        for long in longitude:
            if not isinstance(long, int):
                raise Exception("ERROR: There's a non integer element in the longitude list: " + str(long) + " is a " + str(type(long)))
            if long < -180 or long > 180:
                raise Exception("ERROR: Invalid longitude value (min = -179, max = 179): " + str(long))

        # Validate canTravel
        if not isinstance(canTravel, list):
            raise Exception("ERROR: The canTravel input is not a list (Its actually a " + str(type(canTravel)) + ")")
        if len(canTravel) < 1 or len(canTravel) > 20:
            raise Exception("ERROR: Wrong number of canTravel elements (min = 1, max = 20): " + str(len(canTravel)))
        for ct in canTravel:
            if not isinstance(ct, str):
                raise Exception("ERROR: There's a non-string element in the canTravel list: " + str(ct) + " is a " + str(type(ct)))
            ct_elements = ct.split(' ')
            for airport in ct_elements:
                try:
                    if int(airport) < 0 or int(airport) >= len(canTravel):
                        raise Exception("ERROR: The airport index " + str(airport) + " does not match a valid airport (max airport index = " + str(len(canTravel) - 1) + ")")
                except ValueError:
                    raise Exception("ERROR: The airport index " + str(airport) + " in the canTravel element " + str(ct) + " is not a valid integer. (Its actually a " + str(type(airport)) + ")")

        # Validate origin
        if not isinstance(origin, int):
            raise Exception("ERROR: The origin input is not an integer. " + str(origin) + " is actually a " + str(type(origin)))
        if int(origin) < 0 or int(origin) >= len(canTravel):
            raise Exception("ERROR: Invalid airport defined in origin: " + str(origin) + ". min_airport = 0, max_airport = " + str(len(canTravel)))

        # Validate destination
        if not isinstance(destination, int):
            raise Exception("ERROR: The destination input is not an integer. " + str(destination) + " is actually a " + str(type(destination)))
        if int(destination) < 0 or int(destination) >= len(canTravel):
            raise Exception("ERROR: Invalid airport defined in destination: " + str(destination) + ". min_airport = 0, max_airport = " + str(len(canTravel)))

        # Finally validate if all airports have an unique set of coordinates
        for i in range(0, len(canTravel) - 1):
            airport_latitude = latitude[i]
            airport_longitude = longitude[i]
            for j in range(i + 1, len(canTravel)):
                if latitude[j] == airport_latitude and longitude[j] == airport_longitude:
                    raise Exception("ERROR: There are at least two airports with the same set of coordinates!")

        # Lets process stuff then
        list_of_airports = []
        for i in range(0, len(canTravel)):
            # Create a new airport object for each i-th element of the provided lists
            airport = AirTravel.Airport(i, latitude[i], longitude[i], canTravel[i])
            # And add it to the list of existing airports
            list_of_airports.append(airport)

        # Before moving any further, I can take one special case out of the way
        if origin == destination:
            # Easy
            return 0.0

        # And, once the list is complete, calculate all distances between allowed transits
        self.populate_airport_distances(list_of_airports)

        # I now have all my airports with allowable transfers and respective distances to them in the list_of_airports.
        # Time to calculate stuff
        # Begin by setting the current airport
        current_airport = self.get_airport_by_id(list_of_airports, origin)

        # Create an airplane at the starting airport
        current_airplane = AirTravel.Airplane(current_airport)

        # This method will do its magic and produce a list with airplanes that have traveled all possible routes from
        # origin to destination
        list_of_airplanes = self.travel_to_airport(current_airplane, list_of_airports, [], destination)

        min_distance = -1
        for airplane in list_of_airplanes:
            # Check if the current airplane was able to find a valid route to destination
            if airplane.distance_traveled_so_far != -1:
                if min_distance == -1 or min_distance > airplane.distance_traveled_so_far:
                    # Update the minimum distance found if an airplane was able to go for a valid route that is
                    min_distance = airplane.distance_traveled_so_far

        # Return the final result
        return min_distance

    # This is the method to determine if it is possible to go from airport A to airport B and calculate the shortest distance at it
    # This smells like basic graph theory from afar, and so it is screaming recursivity at this point
    def travel_to_airport(self, current_airplane, list_of_airports, list_of_airplanes, destination):
        if not isinstance(current_airplane, AirTravel.Airplane):
            raise Exception("ERROR: The airplane provided is not from the expected <AirTravel.Airplane> type")

        if not isinstance(list_of_airplanes, list):
            raise Exception("ERROR: The list of airplanes provided is not a list!")

        for airplane in list_of_airplanes:
            if not isinstance(airplane, AirTravel.Airplane):
                raise Exception("ERROR: One of the airplanes in the list of airplanes provided is not a AirTravel.Airplane.")

        if not isinstance(list_of_airports, list):
            raise Exception("ERROR: The list of airports provided is not a list!")

        for airport in list_of_airports:
            if not isinstance(airport, AirTravel.Airport):
                raise Exception("ERROR: One of the airports in the list of airports in not an AirTravel.Airport.")

        # Lets deal with the "terminal" cases before anything else
        # Case 1: I've been around the place with my airplane but now I'm in an airport that allows me to go straight to my destination
        if destination in current_airplane.current_airport.allowed_transits:
            # Get the index of the airport in question
            distance_index = current_airplane.current_airport.allowed_transits.index(destination)
            # Get the distance that I need to travel to get to my destination
            distance_traveled = current_airplane.current_airport.distance_to_transits[distance_index]
            # Put the airplane in the desired airport
            current_airplane.current_airport = self.get_airport_by_id(list_of_airports, destination)
            # Update the distance traveled so far
            current_airplane.distance_traveled_so_far += distance_traveled
            current_airplane.list_of_visited_airports.append(destination)

            # So I'm done with this route (because I've reached my destination). That means that I'm done with this airplane too
            list_of_airplanes.append(current_airplane)

            # And this is going to be my return token: a list with several airplanes, in which some have reach their destination and,
            # hopefully, one of them did it in the most optimized fashion
            return list_of_airplanes

        # Case 2: I can go to other airports from this one but not the one that I want too. In this case, in order to explore all
        # possible routes, I'm going to send this airplane to one of the possible destinations and create a copy of it (I can do
        # this easily with virtual airplanes ah ah) and send them to other destinations to check those routes out
        if destination not in current_airplane.current_airport.allowed_transits:
            # For each possible destination from this point
            for i in range (0, len(current_airplane.current_airport.allowed_transits)):
                # Important fact: as it happens with graphs, no loops are allowed in this case (its very easy to understand why in the
                # context of this problem!). If a certain travel to a certain airport creates a loop, discard it (check the else bellow)
                if current_airplane.current_airport.allowed_transits[i] not in current_airplane.list_of_visited_airports:
                    # Create a copy of the current airplane (I need to since I may travel to multiple places at once)
                    temp_airplane = current_airplane
                    # And execute the trip:
                    temp_airplane.distance_traveled_so_far += current_airplane.current_airport.distance_to_transits[i]
                    temp_airplane.list_of_visited_airports.append(current_airplane.current_airport.allowed_transits[i])
                    temp_airplane.current_airport = self.get_airport_by_id(list_of_airports, current_airplane.current_airport.allowed_transits[i])
                    # And finally recall this method while updating the list of airplanes in the process. That's recursivity for you
                    list_of_airplanes = self.travel_to_airport(temp_airplane, list_of_airports, list_of_airplanes, destination)

                # Case 3: And here goes another terminal case: all my travel possibilities generate graph loops (or simply don't exist because I'm
                # in a terminal airport or something like that)
                else:
                    # Signal that the route defined in current_airplane.list_of_traveled_airports does not go anywhere
                    current_airplane.distance_traveled_so_far = -1
                    # Update the list with the failed airplane
                    list_of_airplanes.append(current_airplane)
                    # And send it back
                    return list_of_airplanes

        return list_of_airplanes

    # To simplify this problem (and its solution) I'm going to create a separate class just for the airports
    class Airport(object):
        def __init__(self, airport_id, airport_latitude, airport_longitude, allowed_transits):
            self.id = airport_id
            self.latitude = airport_latitude
            self.longitude = airport_longitude
            self.allowed_transits = []
            self.distance_to_transits = []

            # Allowed transits should be a string element from the canTravel list
            if not isinstance(allowed_transits, str):
                raise Exception("ERROR: The list of possible transits is not a string!")

            # Breakdown the list of possible transits into individual airport indexes
            possible_transits = allowed_transits.split(' ')
            for possible_transit in possible_transits:
                try:
                    self.allowed_transits.append(int(possible_transit))
                except ValueError:
                    raise Exception("ERROR: The airport index " + str(possible_transit) + " is not possible to cast into integer.")

        # Typical print function for an airport object
        def print(self):
            print ("Airport id = " + str(self.id))
            print ("Airport latitude (degrees) = " + str(self.latitude))
            print ("Airport longitude (degrees) = " + str(self.longitude))
            print ("Allowable transfers: ", end='')
            print (self.allowed_transits)
            print ("Distance to allowed transferes: ", end='')
            print (self.distance_to_transits)
            print ("-------------------------------------------------------\n")

    # Besides the airport class, it turns out that it would be very useful to create an aiplane class too
    class Airplane(object):
        def __init__(self, current_airport):
            if not isinstance(current_airport, AirTravel.Airport):
                raise Exception("ERROR: The airport provided is not from the expected type <AirTravel.Airport>")
            self.current_airport = current_airport
            self.distance_traveled_so_far = 0
            self.list_of_visited_airports = [current_airport.id]

        def travel_to_airport(self, airport_to_travel):
            if not isinstance(airport_to_travel, AirTravel.Airport):
                raise Exception("ERROR: The airport provided is not from the expected type <AirTravel.Airport>")

            if airport_to_travel.id not in self.current_airport.allowed_transits:
                raise Exception("ERROR: The airplane in airport #" + str(self.current_airport.id) + " is not allowed to travel to airport #" + str(airport_to_travel.id))

            # If all is legal then I'm assuming the trip is already done
            distance_index = self.current_airport.allowed_transits.index(airport_to_travel.id)
            travel_distance = self.current_airport.distance_to_transits[distance_index]
            # Update the current airport
            self.current_airport = airport_to_travel
            # The distance traveled so far
            self.distance_traveled_so_far += travel_distance
            # And the list of airports traveled so far
            self.list_of_visited_airports.append(airport_to_travel.id)

    # This method receives a list of airport objects and populates their distance_to_transits list by calculating the distance to each possible transit using the
    # formula provided
    def populate_airport_distances(self, list_of_airports):
        if not isinstance(list_of_airports, list):
            raise Exception("ERROR: The input provided is a " + str(type(list_of_airports)) + " rather than the expected <list> type!")

        for airport in list_of_airports:
            if not isinstance(airport, AirTravel.Airport):
                raise Exception("ERROR: An element from the list of airports is nor an <AirTravel.Airport>")

        for i in range(0, len(list_of_airports)):
            # Grab an airport from the list
            current_airport = list_of_airports[i]

            # And for each allowable transit
            for j in range(0, len(current_airport.allowed_transits)):
                # Get the airport object to which it is possible to travel to
                travel_airport = self.get_airport_by_id(list_of_airports, current_airport.allowed_transits[j])

                # And calculate the respective distances between airports
                current_airport.distance_to_transits.append(self.calculate_distance(current_airport.latitude, current_airport.longitude, travel_airport.latitude, travel_airport.longitude))

    # Another super simple method that receives a set of airports, an return index and return the airport that has that airport id
    def get_airport_by_id(self, list_of_airports, index_to_return):
        for airport in list_of_airports:
            if airport.id == index_to_return:
                return airport

    # This is a standard definition for the distance formula. It receives the needed set of coordinates and returns the distance between them
    def calculate_distance(self, lat1, long1, lat2, long2):
        # Set the planet's radius, though in the wrong units as always... (freakin' imperial miles... who the fudge still uses that?? Dumb americans...)
        radius = 4000

        # OK, so by default the latitude and longitudes came in degrees but the math package formulas all assume the data in radians. Easy problem to solve:
        lat1 = math.radians(lat1)
        lat2 = math.radians(lat2)
        long1 = math.radians(long1)
        long2 = math.radians(long2)

        distance = radius * math.acos(math.sin(lat1) * math.sin(lat2) + math.cos(lat1) * math.cos(lat2) * math.cos(long1 - long2))

        return distance