class SameColorPairs(object):
    min_board = 10
    max_board = 100
    min_color = 2
    max_color = 6
    tile_dict = {}
    removed_tiles = []
    id_multiplier = max_board * min_board

    def removePairs(self, board):
        """
        Main method to process a list of str board
        :param board: list of str - each line of the list contains a string in which each element is the color of the tile in that position
        :return: removed_tiles - a list of all the tile pairs removed in order
        """
        if not isinstance(board, list):
            raise Exception("ERROR: The input board has the wrong type")

        for i in range(0, len(board)):
            if not isinstance(board[i], str):
                raise Exception("ERROR: Row #" + str(i) + " has the wrong type(not a str!)")

            if len(board[i]) < self.min_board or len(board[i]) > self.max_board:
                raise Exception("ERROR: Invalid Width value in line " + str(i) + " (min = " + str(self.min_board) + ", max = " + self.max_board + ")")

            if i > 0:
                if len(board[i]) != len(board[i - 1]):
                    raise Exception("ERROR: The board provided is not a rectangle or a square (line " + str(i) + " has a different length from the rest.")

        if len(board) < self.min_board or len(board) > self.max_board:
            raise Exception("ERROR: Invalid Height value: " + str(len(board)) + " (min = " + str(self.min_board) + ", max = " + str(self.max_board) + ")")
        max_c = len(board[0]) - 1
        colors = self.count_board_colors(board)
        C = len(colors)

        if C < self.min_color or C > self.max_color:
            raise Exception("ERROR: Invalid number of colors in the board: " + str(C) + " (min = " + str(self.min_color) + ", max = " + str(self.max_color) + ")")

        for key in colors:
            color = colors[key]

            if int(color) % 2 != 0:
                raise Exception("ERROR: Color #" + str(key) + " has a odd number of tiles!")

        # Done with the validations

        self.get_tile_board(board)

        if len(self.tile_dict) != len(board) * len(board[0]):
            raise Exception("ERROR: The tile dictionary has a different number of elements from the board.")

        spiral_tiles = self.spiralize_tiles()

        spiral_tiles.reverse()

        # Here's the main algorithm
        start_tiles = len(self.tile_dict)
        end_tiles = -1
        run1 = True

        while start_tiles != end_tiles:

            if run1:
                #################### RUN 1 - REMOVE ADJACENT PAIRS ONLY ####################
                for current_tile in spiral_tiles:
                    # Grab a tile

                    if not current_tile:
                        continue

                    if not current_tile or current_tile.color == -1:
                        continue
                    else:
                        # Here I have a valid tile in current_tile
                        next_tile = current_tile.look_up()
                        if next_tile and next_tile.color == current_tile.color:
                            self.remove_tiles(current_tile, next_tile)
                            continue

                        next_tile = current_tile.look_right()
                        if next_tile and next_tile.color == current_tile.color:
                            self.remove_tiles(current_tile, next_tile)
                            continue

                        next_tile = current_tile.look_down()
                        if next_tile and next_tile.color == current_tile.color:
                            self.remove_tiles(current_tile, next_tile)
                            continue

                        next_tile = current_tile.look_left()
                        if next_tile and next_tile.color == current_tile.color:
                            self.remove_tiles(current_tile, next_tile)
                            continue

                #################### RUN 1 - END ####################
            run1 = False

            # Next run: remove diagonally opposed tiles that form a 4 tile square in which the remaining tiles of that
            # square are either empty cells or cells of the same color (doubtful since the previous sweep removed all
            # possibilities of this happening

            left_over_tiles = self.cleanup_tile_list(spiral_tiles)

            # Take a snapshot of the board before moving further
            start_tiles = len(left_over_tiles)

            checkpoint_start = len(left_over_tiles)
            checkpoint_stop = -1

            while checkpoint_start != checkpoint_stop:
                left_over_tiles = self.cleanup_tile_list(spiral_tiles)
                checkpoint_start = len(left_over_tiles)

                # One more sweep but now just for the remaining tiles
                #################### RUN 2 - REMOVE DIAGONALLY OPPOSED TILES ####################
                for current_tile in left_over_tiles:

                    if current_tile and current_tile.color == -1:
                        continue

                    next_tile = current_tile.look_up_right()
                    if next_tile and next_tile.color == current_tile.color:
                        up_tile = current_tile.look_up()
                        right_tile = current_tile.look_left()

                        if up_tile and right_tile:
                            if up_tile.color == right_tile.color == current_tile.color:
                                self.remove_tiles(current_tile, next_tile)
                                self.remove_tiles(up_tile, right_tile)
                                continue
                            elif up_tile.color == right_tile.color == -1:
                                self.remove_tiles(current_tile, next_tile)
                                continue
                            else:
                                continue
                        else:
                            continue
                    else:
                        continue

                    next_tile = current_tile.look_down_right
                    if next_tile and next_tile.color == current_tile.color:
                        right_tile = current_tile.look_right()
                        down_tile = current_tile.look_down()

                        if right_tile and down_tile:
                            if right_tile.color == down_tile.color == current_tile.color:
                                self.remove_tiles(current_tile, next_tile)
                                self.remove_tiles(right_tile, down_tile)
                                continue
                            elif right_tile.color == down_tile.color == -1:
                                self.remove_tiles(current_tile, next_tile)
                                continue
                            else:
                                continue
                        else:
                            continue
                    else:
                        continue

                    next_tile = current_tile.look_down_left
                    if next_tile and next_tile.color == current_tile.color:
                        down_tile = current_tile.look_down()
                        left_tile = current_tile.look_left()

                        if down_tile and left_tile:
                            if down_tile.color == left_tile.color == current_tile.color:
                                self.remove_tiles(current_tile, next_tile)
                                self.remove_tiles(down_tile, left_tile)
                                continue
                            elif down_tile.color == left_tile.color == -1:
                                self.remove_tiles(current_tile, next_tile)
                                continue
                            else:
                                continue
                        else:
                            continue
                    else:
                        continue

                    next_tile = current_tile.look_up_left()
                    if next_tile and next_tile.color == current_tile.color:
                        left_tile = current_tile.look_left()
                        up_tile = current_tile.look_up()
                        if left_tile and up_tile:
                            if left_tile.color == up_tile.color == current_tile.color:
                                self.remove_tiles(current_tile, next_tile)
                                self.remove_tiles(left_tile, up_tile)
                                continue
                            elif left_tile.color == up_tile.color == -1:
                                self.remove_tiles(current_tile, next_tile)
                                continue
                            else:
                                continue
                        else:
                            continue
                    else:
                        continue

                #################### RUN 2 - END ####################

                # Refresh the remaining tiles list
                left_over_tiles = self.cleanup_tile_list(spiral_tiles)

                # And now check lines
                #################### RUN 3 - TILES IN THE SAME LINE ####################
                for current_tile in left_over_tiles:
                    if not current_tile or current_tile.color == -1:
                        continue

                    next_tile = current_tile.look_up()

                    while next_tile and next_tile.color == -1:
                        next_tile = next_tile.look_up()

                    if next_tile and next_tile.color == current_tile.color:
                        self.remove_tiles(current_tile, next_tile)
                        continue

                    next_tile = current_tile.look_right()

                    while next_tile and next_tile.color == -1:
                        next_tile = next_tile.look_right()

                    if next_tile and next_tile.color == current_tile.color:
                        self.remove_tiles(current_tile, next_tile)
                        continue

                    next_tile = current_tile.look_down()

                    while next_tile and next_tile.color == -1:
                        next_tile = next_tile.look_down()

                    if next_tile and next_tile.color == current_tile.color:
                        self.remove_tiles(current_tile, next_tile)
                        continue

                    next_tile = current_tile.look_left()

                    while next_tile and next_tile.color == -1:
                        next_tile = next_tile.look_left()

                    if next_tile and next_tile.color == current_tile.color:
                        self.remove_tiles(current_tile, next_tile)

                left_over_tiles = self.cleanup_tile_list(spiral_tiles)

                #################### RUN 3 - END ####################

                #################### RUN 4 - TILES IN THE SAME BOUNDING RECTANGLE ####################
                # Bounding rectangle computation
                for i in range(0, len(left_over_tiles) - 1):
                    if left_over_tiles[i] and left_over_tiles[i].color != -1:

                        for j in range(i + 1, len(left_over_tiles)):
                            if left_over_tiles[j] and left_over_tiles[j].color == left_over_tiles[i].color:
                                if self.validate_bounding_rectangle(left_over_tiles[i], left_over_tiles[j]):
                                    self.remove_tiles(left_over_tiles[i], left_over_tiles[j])
                                    left_over_tiles[i].color = -1
                                    left_over_tiles[j].color = -1
                            else:
                                continue
                left_over_tiles = self.cleanup_tile_list(spiral_tiles)
                checkpoint_stop = len(left_over_tiles)

                #################### RUN 4 - END ####################
            # Count the tiles still left before running another loop
            left_over_tiles = self.cleanup_tile_list(spiral_tiles)
            end_tiles = len(left_over_tiles)

        return self.removed_tiles

    def convert_dictionary_to_list(self):
        """
        Simple method to convert and return a list made out of all the tiles in self.tile_dict
        :return: tile_list: a list with all the tiles in the internal dictionary ordered by their is
        """

        tile_list = []
        for key in self.tile_dict:
            tile_list.append(self.tile_dict[key])

        return tile_list

    def cleanup_tile_list(self, tile_list):
        """
        Method to remove all "deleted" tiles from a list of tiles, i.e, tiles whose color is now -1
        :param tile_list: a list with SameColorPairs.Tile objects
        :return: the input list minus all elements whole tile.color == -1
        """

        for tile in tile_list:
            if tile.color == -1:
                tile_list.remove(tile)

        return tile_list

    def spiralize_tiles(self):
        """
                This method organises the tiles (well, their ids actually) in a list such as, when removing it from end to start (using list.pop()) it follows a spiral pattern from the centre tile all the way up to one of the corners
        :return: spiral_tiles - list with the tiles's id organized in a spiral fashion
        """

        if len(self.tile_dict) == 0:
            raise Exception("ERROR: The tile dictionary is still empty.")

        spiral_tiles = []

        current_tile = self.tile_dict[0]

        while len(spiral_tiles) != len(self.tile_dict) - 1:

            next_tile = current_tile.look_right()

            while next_tile and next_tile not in spiral_tiles:
                spiral_tiles.append(current_tile)
                current_tile = next_tile
                next_tile = current_tile.look_right()

            next_tile = current_tile.look_down()

            while next_tile and next_tile not in spiral_tiles:
                spiral_tiles.append(current_tile)
                current_tile = next_tile
                next_tile = current_tile.look_down()

            next_tile = current_tile.look_left()

            while next_tile and next_tile not in spiral_tiles:
                spiral_tiles.append(current_tile)
                current_tile = next_tile
                next_tile = current_tile.look_left()

            next_tile = current_tile.look_up()

            while next_tile and next_tile not in spiral_tiles:
                spiral_tiles.append(current_tile)
                current_tile = next_tile
                next_tile = current_tile.look_up()

        spiral_tiles.append(current_tile)

        return spiral_tiles

    def validate_bounding_rectangle(self, tile1, tile2):
        if not tile1 or not tile2:
            raise Exception("ERROR: One of the tiles is invalid (NoneType)")

        # The tiles are in a vertical or horizontal line. The previous loop should have eliminated them
        # if the line was empty. Which means that the tiles have a non empty, different colored tile somewhere
        # between them
        if tile1.r == tile2.r or tile1.c == tile2.c:
            return False

        min_r = min(tile1.r, tile2.r)
        min_c = min(tile1.c, tile2.c)

        max_r = max(tile1.r, tile2.r)
        max_c = max(tile1.c, tile2.c)

        for r in range(min_r, max_r + 1):
            for c in range(min_c, max_c + 1):
                temp_tile = self.tile_dict.get(r * self.id_multiplier + c)

                if not temp_tile:
                    raise Exception("ERROR: The tile at ({0}, {1}) does not exist!".format(str(r), str(c)))

                if temp_tile.color != -1 and temp_tile.color != tile1.color:
                    return False
        return True

    def get_tile_board(self, board):
        """
        This method receives a board in the list(str) format and populates the internal dictionary with tile objects
        created from the data in the input board
        :param board: list of str
        :return: None - the method simply populates the SameColorPairs.tile_dict structure
        """
        for r in range(0, len(board)):
            for c in range(0, len(board[0])):

                if str(board[r][c]) == 'X':
                    self.tile_dict[r * self.id_multiplier + c] = self.Tile(r, c, -1)
                else:

                    try:
                        if int(board[r][c]) < 0 or int(board[r][c]) > self.max_color:
                            raise Exception("ERROR: Invalid color value at r = {0}, c = {1}".format(str(r), str(c)))
                    except ValueError:
                        raise Exception("ERROR: Position r = {0}, c = {1} has an invalid element! (not a int)".format(str(r), str(c)))

                    self.tile_dict[r * self.id_multiplier + c] = self.Tile(r, c, int(board[r][c]))

    def get_remaining_tiles(self):
        """
        Method that sorts into a list all tiles that haven't been removed so far, i.e, tile.color != -1
        :return: remainin_tiles - a list with all the tiles still left to remove
        """
        remaining_tiles = []

        for key in self.tile_dict:
            tile = self.tile_dict[key]

            if tile != None and tile.color != -1:
                remaining_tiles.append(tile)

        return remaining_tiles

    def count_board_colors(self, board):
        """
        Method that counts how many different colors are in the input board
        :param board: list of str
        :return: colors - a list in which the position of each element represents a color present in the board. The value of each element is the number
        of tiles of that given color present in the board
        """
        colors = {}

        for r in range(0, len(board)):
            for c in range(0, len(board[0])):
                try:
                    int(board[r][c])
                except ValueError:
                    continue

                if int(board[r][c]) == -1:
                    continue

                try:
                    colors[int(board[r][c])] += 1
                except KeyError:
                    colors[int(board[r][c])] = 1

        return colors

    def remove_tiles(self, tile1, tile2):
        """
        Method to remove two tiles from the dictionary. This removal is only virtual, i.e, the tile's color is set to -1
         which implies an empty cell in the board
        :param tile1: SameColorPairs.Tile()
        :param tile2: SameColorPairs.Tile()
        :return: None
        """

        tile1.color = -1
        tile2.color = -1

        # Also, to simplify things, the removal operation also adds the removed pair to the list of remove tiles
        self.removed_tiles.append("{0} {1} {2} {3}".format(tile1.r, tile1.c, tile2.r, tile2.c))

    def print_dictionary(self):
        """
        This method print all elements in the internal dictionary
        :return: None
        """

        for key in self.tile_dict:
            self.tile_dict[key].print()

        print()

    def print_tile_dictionary(self, max_c):
        """
        This method prints the contents of the internal tile dictionary in a human readable format, i.e, like a normal board
        :param max_c: int
        :return: None
        """
        board = []
        s = ""

        for key in self.tile_dict:
            tile = self.tile_dict[key]

            if tile.color == -1:
                s += 'X'
            else:
                s += str(tile.color)

            if tile.c == max_c:
                board.append(s)
                s = ""

        for line in board:
            print(line)

    class Tile(object):
        def __init__(self, row, column, color):
            """
            Initialization method: it first searches for a tile with that id. If that tile already exists, it is returned. Otherwise
             it is going to get created first and then returned
            :param row: int
            :param column: int
            :param color: int
            """
            temp_tile = SameColorPairs.tile_dict.get(row * SameColorPairs.id_multiplier + column)

            if not temp_tile:
                self.id = int(row * SameColorPairs.id_multiplier + column)
                self.r = row
                self.c = column
                self.color = color

                SameColorPairs.tile_dict[self.id] = self

        def print(self):
            """
            Simple print method
            :return: None
            """
            print("Id = {0}, row = {1}, column = {2}, color = {3}".format(self.id, self.r, self.c, self.color))

        def look_up(self):
            """
            Method to return the tile immediately above this one. Return None if it is at the board's edge
            :return: SameColorPairs.Tile() or None if the key is invalid
            """
            return SameColorPairs.tile_dict.get(int((self.r - 1) * SameColorPairs.id_multiplier + self.c))

        def look_right(self):
            """
            Method to return the tile immediately to the right of this one. Return None if it is at the board's edge
            :return: SameColorPairs.Tile() or None if the key is invalid
            """
            return SameColorPairs.tile_dict.get(int(self.r * SameColorPairs.id_multiplier + (self.c + 1)))

        def look_down(self):
            """
            Method to return the tile immediately down of this one. Return None if it is at the board's edge
            :return: SameColorPairs.Tile() or None if the key is invalid
            """
            return SameColorPairs.tile_dict.get(int((self.r + 1) * SameColorPairs.id_multiplier + self.c))

        def look_left(self):
            """
            Method to return the tile immediately to the left of this one. Return None if it is at the board's edge
            :return: SameColorPairs.Tile() or None if the key is invalid
            """
            return SameColorPairs.tile_dict.get(int(self.r * SameColorPairs.id_multiplier + (self.c - 1)))

        def look_up_right(self):
            """
            Method to return the tile immediately up-right of this one. Return None if it is at the board's edge
            :return: SameColorPairs.Tile() or None if the key is invalid
            """
            return SameColorPairs.tile_dict.get(int((self.r - 1) * SameColorPairs.id_multiplier + (self.c + 1)))

        def look_down_right(self):
            """
            Method to return the tile immediately down-right of this one. Return None if it is at the board's edge
            :return: SameColorPairs.Tile() or None if the key is invalid
            """
            return SameColorPairs.tile_dict.get(int((self.r + 1) * SameColorPairs.id_multiplier + (self.c + 1)))

        def look_down_left(self):
            """
            Method to return the tile immediately down_left of this one. Return None if it is at the board's edge
            :return: SameColorPairs.Tile() or None if the key is invalid
            """
            return SameColorPairs.tile_dict.get(int((self.r + 1) * SameColorPairs.id_multiplier + (self.c - 1)))

        def look_up_left(self):
            """
            Method to return the tile immediately up-left of this one. Return None if it is at the board's edge
            :return: SameColorPairs.Tile() or None if the key is invalid
            """
            return SameColorPairs.tile_dict.get(int((self.r - 1) * SameColorPairs.id_multiplier + (self.c - 1)))
