import AirTravel_src.AirTravel as airtravel

latitudes = [
    [0, 0, 70],
    [0, 0, 70],
    [0, 30, 60],
    [0, 20, 55]
]

longitudes = [
    [90, 0, 45],
    [90, 0, 45],
    [25, -130, 78],
    [-20, 85, 42]
]

canTravels = [
    ["2", "0 2", "0 1"],
    ["1 2", "0 2", "0 1"],
    ["1 2", "0 2", "1 2"],
    ["1", "0", "0"]
]

origins = [
    0,
    0,
    0,
    0
]

destinations = [
    1,
    1,
    0,
    2
]

if __name__ == "__main__":
    at = airtravel.AirTravel()

    for i in range(0, len(canTravels)):
        shortest_route = at.shortestTrip(latitudes[i], longitudes[i], canTravels[i], origins[i], destinations[i])
        print ("Case #" + str(i))
        print ("Shortest distance = " + str(shortest_route) + " miles.")