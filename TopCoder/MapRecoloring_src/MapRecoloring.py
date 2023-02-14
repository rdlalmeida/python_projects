class MapRecoloring(object):
    dim_min = 20
    dim_max = 200
    id_multiplier = dim_max * 10        # I'll use this value to create unique id values for each tile in the board
    tile_dict = {}
    region_dict = {}

    def recolor(self, H, regions, oldColors):
        """
        Main method to reorganize the board
        :param H: The height of the board (integer)
        :param regions: A board map with the different regions identified numerically
        :param oldColors: Another board map but stating the colors of each cell in the map, also numerically.
        :return: An array with the colors that each region has
        """
        # Validation phase
        if H < self.dim_min or H > self.dim_max:
            raise Exception("ERROR: Board height out of bounds: {0} (min = {1}, max = {2})".format(str(H), str(self.dim_min), str(self.dim_max)))

        tile_count = len(regions)

        if len(oldColors) != tile_count:
            raise Exception("ERROR: Size mismatch between regions and oldColors!")

        W = int(tile_count/H)

        if W < self.dim_min or W > self.dim_max:
            raise Exception("ERROR: Board width out of bounds: {0} (min = {1}, max = {2})".format(str(W), str(self.dim_min), str(self.dim_max)))

        reg_min = tile_count/50
        reg_max = tile_count/10

        regions_count = sorted(self.calculate_regions(regions))

        if len(regions_count) < reg_min or len(regions_count) > reg_max:
            raise Exception("ERROR: The board has an illegal number of regions: {0} (min = {1}, max = {2})".format(str(len(regions)), str(reg_min), str(reg_max)))

        # Done with the validations

        # Begin with the tile conversion and storage
        self.create_tiles(W, regions, oldColors)

        # Next comes the regions
        self.populate_regions(regions_count)

        # The populate the surrounding regions for each region
        self.populate_region_neighbors()

        # And now for the final step: color each region accordingly
        regions_colors = self.color_regions()

        return regions_colors

    def color_regions(self):
        """
        This method continues the logic so far. With the internal region dictionary filled out properly, I can now analyse the tiles in
        each region and determine a color for each region
        :return: regions_colors: The intended result for this problem. That's a list with R integers in which the ith element indicates
        the color of the ith region
        """

        region_colors = []

        for region_key in self.region_dict:
            current_region = self.region_dict[region_key]

            region_colors_count = []

            # This for loop populates the region_colors_count list with as many colors as regions, assuming a priori the worst case
            # scenario in which I would have to color each region with a different color from the rest
            for region in self.region_dict:
                region_colors_count.append(0)

            for tile_key in current_region.tile_dict:
                tile = current_region.tile_dict[tile_key]

                try:
                    region_colors_count[tile.color] += 1
                except IndexError:
                    raise Exception("ERROR: There was a problem in the color count calculation: there are still some unmapped colors in the board!")

            # At this point I have a list with the number of tiles per color in this region. This allows me to organize this information
            # in a way that facilitates the color attribution per region.

            for i in range(0, len(region_colors_count)):
                # Populate the return list with a three element tuple with the following format: (region.id, color, priority) where
                # priority is the quotient between the number of tiles of that color in that region and the total number of tiles
                # in that region. This parameter is going to be used to minimize the number of tile recolors necessary
                region_colors.append((current_region.id, i, region_colors_count[i]/sum(region_colors_count)))

        # Order the tuples per decreasing order of priority value
        region_colors = sorted(region_colors, key=lambda item: item[2], reverse=True)

        colored_regions = []

        for item in region_colors:
            if len(colored_regions) == len(self.region_dict):
                break

            # Grab the region, which is indicated by the first element of the tuple
            current_region = self.region_dict.get(item[0])

            if not current_region:
                raise Exception("ERROR: There's a non-existent region in the color profile list!")

            if current_region.color != -1:
                continue
            else:
                # Set the color flag
                valid_color = True

                # Check all colored regions so far
                for i in range(0, len(colored_regions)):
                    # If the current color has been set already and the current region borders that region
                    if colored_regions[i].color == item[1] and current_region.id in colored_regions[i].surrounding_regions:
                        # Invalidate the color to this region by setting this flag to False
                        valid_color = False
                        break

                # If the color can be set to the region
                if valid_color:
                    # Set the color to that region
                    current_region.color = item[1]
                    # And add this region to the colored list
                    colored_regions.append(current_region)

        region_colors = []
        for region_key in self.region_dict:
            region_colors.append(self.region_dict.get(region_key).color)

        return region_colors

    def check_previous_regions(self, color, current_region):
        """
        This method checks the current color against all regions that have come before current_regions (MapRecoloring.Regions have a unique
        and sequential id that allows this) and returns True if it is possible to set the current color to the current region or False otherwise
        :param color: color integer for the color that is to be set to this region
        :param current_region: the region in question
        :return: True or False
        """

        for reg_index in range(0, current_region.id):
            previous_region = self.region_dict.get(reg_index)

            if not previous_region:
                raise Exception("ERROR: Region #{0} is missing from the region set!".format(str(reg_index)))

            # Check for adjacent regions that have the color that I want to set
            if current_region.id in previous_region.surrounding_regions and color == previous_region.color:
                return False

        return True

    def populate_region_neighbors(self):
        """
        This method goes to each one of the MapRecoloring.Region objects in the internal region dictionary and determines which
        other regions border this one
        :return: Nothing. The internal MapRecoloring.Region.surrounding_regions list is filled out
        """

        for reg_key in self.region_dict:
            current_region = self.region_dict[reg_key]

            for tile_key in current_region.tile_dict:
                current_tile = current_region.tile_dict[tile_key]

                next_tile = current_tile.look_up()

                if next_tile and next_tile.region != current_tile.region and next_tile.region not in current_region.surrounding_regions:
                    current_region.surrounding_regions.append(next_tile.region)

                next_tile = current_tile.look_right()

                if next_tile and next_tile.region != current_tile.region and next_tile.region not in current_region.surrounding_regions:
                    current_region.surrounding_regions.append(next_tile.region)

                next_tile = current_tile.look_down()

                if next_tile and next_tile.region != current_tile.region and next_tile.region not in current_region.surrounding_regions:
                    current_region.surrounding_regions.append(next_tile.region)

                next_tile = current_tile.look_left()

                if next_tile and next_tile.region != current_tile.region and next_tile.region not in current_region.surrounding_regions:
                    current_region.surrounding_regions.append(next_tile.region)

            current_region.surrounding_regions = sorted(current_region.surrounding_regions)

    def populate_regions(self, regions_count):
        """
        This method receives a list with all the counted regions (obtainable with self.calculate_regions method) and populates
        the internal regions_dict dictionary
        :param regions_count: a list identifying how many regions and what are their numbers for the current board.
        :return: None. The populated structure is internal to the MapRecoloring objects
        """

        for region in regions_count:
            self.region_dict[region] = MapRecoloring.Region(region)

        for key in self.tile_dict:
            tile = self.tile_dict[key]

            self.region_dict[tile.region].add_tile(tile)

    def create_tiles(self, W, regions, oldColors):
        """
        This method populates the internal tile_dict dictionary with HxW MapRecoloring.Tile objects
        :param regions: Board list with the regions to which each tile belongs
        :param oldColors: Board list with the color of each tile
        :return: None. The dictionary is a built-in one with the MapRecoloring object
        """

        for i in range(0, len(regions)):
            tile = MapRecoloring.Tile(int(i/W), int(i%W), regions[i], oldColors[i])
            self.tile_dict[tile.id] = tile

    def calculate_colors(self, oldColors):
        """
        Method to determine the spectrum of colors available in this board
        :param oldColors: Board map with all the colors of each tile
        :return: colors_count: a list with all detected colors
        """

        colors_count = []

        for r in range(0, len(oldColors)):
            for c in range(0, len(oldColors[0])):
                if oldColors[r][c] not in colors_count:
                    colors_count.append(oldColors[r][c])

        return colors_count

    def calculate_regions(self, regions):
        """
        Method to calculate, explicitly, the number of regions in the board.
        :param regions: Board map with a numerical representation of the regions.
        :return: A list with all identified (and sorted) region numbers for that board.
        """
        regions_count = []

        for r in regions:
            if r not in regions_count:
                regions_count.append(r)

        return sorted(regions_count)

    class Tile(object):
        """
        Main interable for this problem. Each board is going to be abstracted into a set of tiles objects.
        """
        def __init__(self, row, column, region, color):
            """
            Initialization method. Creates a tile object using the parameters provided
            :param row: Vertical position of the tile
            :param column: Horizontal position of the tile
            :param region: Region to which the tile belongs.
            :param color: Current color attributed to this tile
            """
            self.r = row
            self.c = column
            self.color = color
            self.region = region
            self.id = row * MapRecoloring.id_multiplier + column

        def print(self):
            """
            Basic printing method
            :return: None
            """
            print("Tile id#{0}, row = {1}, column = {2}, color = {3}, region = {4}".format(str(self.id), str(self.r), str(self.c), str(self.color), str(self.region)))

        def look_up(self):
            """
            Method to obtain the tile immediately above this one
            :return: The tile above this one or None if there is any (board edge)
            """
            return MapRecoloring.tile_dict.get((self.r - 1) * MapRecoloring.id_multiplier + self.c)

        def look_left(self):
            """
            Method to obtain the tile immediately left of this one
            :return: The tile left of this one or None if there is any (board edge)
            """
            return MapRecoloring.tile_dict.get(self.r * MapRecoloring.id_multiplier + (self.c - 1))

        def look_down(self):
            """
            Method to obtain the tile immediately down of this one
            :return: The tile down of this one or None if there is any (board edge)
            """
            return MapRecoloring.tile_dict.get((self.r + 1) * MapRecoloring.id_multiplier + self.c)

        def look_right(self):
            """
            Method to obtain the tile immediately right of this one
            :return: The tile right of this one or None if there is any (board edge)
            """
            return MapRecoloring.tile_dict.get(self.r * MapRecoloring.id_multiplier + (self.c + 1))

    class Region(object):
        """
        A Region object is going to be basically the set of tiles that define it
        """
        def __init__(self, region_id):
            self.id = region_id
            self.color = -1
            self.tile_dict = {}
            self.surrounding_regions = []

        def print(self):
            """
            Basic printing method
            :return:
            """
            print("Region id = {0}, color = {1} has {2} tiles and borders {3} other regions.".format(str(self.id), str(self.color), str(len(self.tile_dict)), str(len(self.surrounding_regions))))

        def printall(self):
            """
            Extends the basic printing method by printing the tile and surrounding regions dictionaries too
            :return: None
            """
            self.print()
            print("List of tiles in this region:")

            for tile_key in self.tile_dict:
                self.tile_dict.get(tile_key).print()

            print("\nSurrounding regions: ", end='')
            for region in self.surrounding_regions:
                print("{0} ".format(str(region)), end='')

            print("\n----------------------------------------------------------------------------------------\n")

        def add_tile(self, tile):
            if not isinstance(tile, MapRecoloring.Tile):
                raise Exception("ERROR: Wrong input type: {0} (not a MapRecoloring.Tile".format(str(type(tile))))

            self.tile_dict[tile.id] = tile

        def get_size(self):
            return len(self.tile_dict)

import sys

H = int(input())
S = int(input())
regions = []

for i in range(S):
    regions.append(int(input()))

R = int(input())
oldColors = []

for i in range(R):
    oldColors.append(int(input()))

mr = MapRecoloring()
ret = mr.recolor(H, regions, oldColors)

print(len(ret))

for num in ret:
    print(num)

sys.stdout.flush()