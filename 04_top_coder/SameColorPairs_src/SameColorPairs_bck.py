import SameColorPairs_src.BoardGenerator as bg

class SameColorPairs(object):
    min_board = 10
    max_board = 100
    min_color = 2
    max_color = 6

    def removePairs(self, board):
        # To simplify matters, I'm going to do all input validations on this method since it is going to act as a gateway to all remaining ones
        if not isinstance(board, list):
            raise Exception("ERROR: The input board has the wrong type (not a list!)")

        for i in range(0, len(board)):
            if not isinstance(board[i], str):
                raise Exception("ERROR: Row #" + str(i) + " has the wrong format (not a str!)")

        if len(board) < self.min_board or len(board) > self.max_board:
            raise Exception("ERROR: Invalid Height value: " + str(len(board)) + " (min = 10, max = 100)")

        if len(board[0]) < self.min_board or len(board[0]) > self.max_board:
            raise Exception("ERROR: Invalid Width value: " + str(len(board[0])) + " (min = 10, max = 100)")

        C = self.count_board_colors(board)

        if C < self.min_color or C > self.max_color:
            raise Exception("ERROR: Invalid number of colors on the board: " + str(C) + " (min = 2, max = 6)")

        # Check also the eveness of the tiles regarding their color
        if not self.check_board_parity(board, C):
            raise Exception("ERROR: There is a color that has an odd number of tiles!")

        # Done with all validations
        tile_dict = self.create_tile_board(board)
        done = False

        # The list of tile to remove is going to be stored here
        results = []

        # I'm gonna try to remove tiles from the board using this loop. There are two stop conditions:
        # Either I run out of tiles or I get to a point where I can't do anything else. When that happens
        # I'm gonna flag that situation and get out of this cycle
        while self.get_board_size(tile_dict) > 0 and not done:
            done = True                 # Set the flag before anything else.

            # Circle through all colors
            for color in range(0, C):
                # I need to run this loop to each available color to maximize board tile removal
                # Start by scanning the tile board
                for key in tile_dict:
                    try:
                        # Retrieve a tile
                        current_tile = tile_dict[key]
                    except KeyError:
                        continue
                        # Proceed forward only if the tile is from the color that I'm processing currently,
                        # it wasn't removed already and its surrounded by empty cells and/or tiles with the same color
                    if current_tile.color != color or current_tile.color == -1:
                            # If the tile is not valid, carry on to the next one
                        continue
                        # Check if he tile at hand is surrounded only by empty cells, i.e, is an island (and also make sure it is not
                        # the last tile on the board)
                    elif current_tile.validate_tile():
                        # Retrieve the mapping for all valid surrounding tiles
                        dir_map = self.get_dir_map(current_tile)

                        for direction in dir_map:
                            # Retrieve a tile to which I can form an bounding rectangle with
                            next_tile = tile_dict[dir_map[direction]]

                            # Process the corresponding bounding rectangle. If a valid bounding rectangle is found
                            removed_tiles = self.remove_adjacent_pairs(current_tile, next_tile, tile_dict)

                            if len(removed_tiles) > 0:
                                # Since I've successfully removed two tiles from the board, the overall board configuration
                                # was changed, which means that new removable pairs may be available now. Set the done flag
                                # to force the while loop to do at least one more go
                                done = False
                                # Format the removed pair coordinates and add it to the return list
                                for pair in removed_tiles:
                                    results.append(pair)
                            else:
                                continue
                    else:
                        # This one is a tricky subcase that I need to process in a different way
                        # In this case I have a tile surrounded by empty tiles and/or different colors.
                        # I need to get another tile of the same color
                        result = self.check_tile_lines(current_tile, tile_dict, len(board), len(board[0]))

                        if result == "":
                            continue
                        else:
                            results.append(result)
                            done = False

        return results

    # Method to explore all rectangle possibilities within a list of tiles of the same color in a given board
    def explore_bounding_rectangles(self, list_of_tiles, tile_dict, result):
        # Check if the list has at least two tiles left
        if len(list_of_tiles) > 2:
            # Set up the indexes
            first_index = 0
            second_index = 1

            # And retrieve the first two tiles of it
            first_tile = list_of_tiles[first_index]
            second_tile = list_of_tiles[second_index]

            # And determine the corresponding bounding rectangle
            bdr = self.check_bounding_rectangle(first_tile, second_tile, tile_dict)

            # Run the next loop while there are still tiles in the list to check out or
            # a valid pair of tiles has been found
            while bdr == "" and first_index < len(list_of_tiles):
                # Move to the next tile
                second_index += 1

                # And protect the loop against indexing out of bounds
                if second_index >= len(list_of_tiles):
                    first_index += 1

                    # If my first index points to the last tile on the list
                    if first_index == len(list_of_tiles) - 1:
                        # There's nothing left to do here
                        break
                    else:
                        first_tile = list_of_tiles[first_index]
                        second_index = first_index + 1

                second_tile = list_of_tiles[second_index]

                bdr = self.check_bounding_rectangle(first_tile, second_tile, tile_dict)

            # At this point, either I have a valid bounding rectangle (bdr != "") or I've gone through the whole
            # list without removing any tiles
            if bdr != "":
                # Remove the removed tiles from the main list
                list_of_tiles.remove(first_tile)
                list_of_tiles.remove(second_tile)
                # Add the latest results to the result list
                result.append(bdr)

                # If there are still tiles left in the list
                if len(list_of_tiles) > 0:
                    # Check out the rest of it first
                    result = self.explore_bounding_rectangles(list_of_tiles, tile_dict, result)
                    return result
                else:
                    # If the list is empty, return all results so far
                    return result
            # If I went through the whole list without finding a single valid bounding rectangle
            else:
                # Return whatever I have found so far
                return result
        else:
            return result

    # This method receives a tile and the dictionary of tiles. Then it checks above, left, right and down from the tile for a
    # line of empty cells that can lead to a tile of the same color and thus removeable
    def check_tile_lines(self, tile, tile_dict, H, W):
        base_r = tile.row
        base_c = tile.column

        # Check above
        if base_r > 0:
            for r in range(base_r - 1, -1, -1):
                next_tile = tile_dict[r * self.max_board + base_c]

                if next_tile.color == -1:
                    continue
                elif next_tile.color != tile.color:
                    return ""
                else:
                    return str(base_r) + " " + str(base_c) + " " + str(next_tile.row) + " " + str(next_tile.column)

        # Check bellow
        if base_r < H - 1:
            for r in range(base_r + 1, H):
                next_tile = tile_dict[r * self.max_board + base_c]

                if next_tile.color == -1:
                    continue
                elif next_tile.color != tile.color:
                    return ""
                else:
                    return str(base_r) + " " + str(base_c) + " " + str(next_tile.row) + " " + str(next_tile.column)

        # Check left
        if base_c > 0:
            for c in range(base_c - 1, -1, -1):
                next_tile = tile_dict[base_r * self.max_board + c]

                if next_tile.color == -1:
                    continue
                elif next_tile.color != tile.color:
                    return ""
                else:
                    return str(base_r) + " " + str(base_c) + " " + str(next_tile.row) + " " + str(next_tile.column)

        # Check_right
        if base_c < W - 1:
            for c in range(base_c + 1, W):
                next_tile = tile_dict[base_r * self.max_board + c]

                if next_tile.color == -1:
                    continue
                elif next_tile.color != tile.color:
                    return ""
                else:
                    return str(base_r) + " " + str(base_c) + " " + str(next_tile.row) + " " + str(next_tile.column)

        # If I got here than the tile has nothing but empty cells on all four surrounding directions
        return ""

    # Method to update a list of tiles to remove by checking the corresponding result list and removing any duplicates on that list
    def update_list_of_tiles(self, list_of_tiles, results, tile_dict):
        for line in results:
            # Split the result line into 4 tokens: r1, c1, r2 and c2
            tokens = line.split(' ')
            if len(tokens) != 4:
                raise Exception("ERROR: Result line badly formatted: " + str(line))

            # Grab the corresponding tiles from the dictionary
            tile1 = tile_dict[tokens[0] * self.max_board + tokens[1]]
            tile2 = tile_dict[tokens[2] * self.max_board + tokens[3]]

            if tile1 in list_of_tiles:
                # And remove them from the list if they are still there
                list_of_tiles.remove(tile1)

            if tile2 in list_of_tiles:
                list_of_tiles.remove(tile2)

        # And return the updated list back
        return list_of_tiles


    # Method that computes and returns all remaining tiles still in the board after some removals have been made
    def get_remaining_tiles(self, tile_dict, color):
        remaining_tiles = []

        for key in tile_dict:
            temp_tile = tile_dict[key]

            if temp_tile.color != -1 and temp_tile.color == color:
                # Add any valid tiles to the corresponding color row
                remaining_tiles.append(temp_tile)

        return remaining_tiles

    # This method receives two tiles that occupy corners of a bounding rectangle, determines if it contains tiles
    # of other colors and remove the tiles if so. It return the removed pair in the defined str format
    def check_bounding_rectangle(self, tile1, tile2, tile_dict):
        # The logic here is an extension of the adjacent tile removal method

        # Case 1: The tiles are in the same row
        if tile1.row == tile2.row:
            if tile1.column < tile2.column:
                left_tile = tile1
                right_tile = tile2
            else:
                left_tile = tile2
                right_tile = tile1

            # Scan the line
            for c in range(left_tile.column + 1, right_tile.column):
                # If somewhere down that line I can find a non-empty, different colored tile
                if tile_dict[tile1.row * self.max_board + c].color != -1 and tile_dict[tile1.row * self.max_board + c].color != tile1.color:
                    # No can do
                    return ""

            # If I can get to this point, then the line is empty and I can remove the tiles
            self.remove_tiles(tile1, tile2, tile_dict)
            return str(tile1.row) + " " + str(tile1.column) + " " + str(tile2.row) + " " + str(tile2.column)

        # Case 2: The tiles are in the same column
        elif tile1.column == tile2.column:
            if tile1.row < tile2.row:
                top_tile = tile1
                bottom_tile = tile2
            else:
                top_tile = tile2
                bottom_tile = tile1

            # Scan the column
            for r in range(top_tile.row + 1, bottom_tile.row):
                # Again, check for non-empty, different colored tiles
                if tile_dict[r * self.max_board + tile1.column].color != -1 and tile_dict[r * self.max_board + tile1.column].color != tile1.color:
                    return ""

            # Got to this spot. The column is empty
            self.remove_tiles(tile1, tile2, tile_dict)
            return str(tile1.row) + " " + str(tile1.column) + " " + str(tile2.row) + " " + str(tile2.column)

        # Case 3: The two tiles are in corners of a rectangle
        else:
            # The other corners of the rectangle are given by
            r1 = tile1.row
            c1 = tile1.column
            r2 = tile2.row
            c2 = tile2.column

            rmin = min(r1, r2)
            cmin = min(c1, c2)

            rmax = max(r1, r2)
            cmax = max(c1, c2)

            # My bounding rectangle is now defined between the coordinates (rmin, cmin) and (rmax, cmax)
            for r in range(rmin, rmax + 1):
                for c in range(cmin, cmax + 1):
                    # Jump over tile1 and tile2
                    if (r == r1 and c == c1) or (r == r2 and c == c2):
                        continue
                    # Check for non-empty, different colored tiles along the rectangle
                    elif tile_dict[r * self.max_board + c].color != -1 and tile_dict[r * self.max_board + c].color != tile1.color:
                        return ""

            # If none were found
            self.remove_tiles(tile1, tile2, tile_dict)
            return str(r1) + " " + str(c1) + " " + str(r2) + " " + str(c2)

    # Method to calculate how many tiles are still on the board. Since I'm not "physically" removing any tiles, I need
    # a function to compute the number of tiles still left on the board (tile.color != -1)
    def get_board_size(self, tile_dict):
        count = 0
        for key in tile_dict:
            if tile_dict[key].color != -1:
                count += 1

        return count

    # Method to return the direction map of a tile, which is a dictionary that matches directions with the corresponding
    # tile id in regard to the current tile, which makes fetching surroundind tiles easier
    def get_dir_map(self, tile):
        dir_map = {}
        r = tile.row
        c = tile.column

        for key in tile.sc:
            try:
                # Create a direction mapping only for valid surrounding tiles
                # By using max_board as a multiplier in the tile id calculation, I guarantee that,
                # for a max 100x100 board, every tile has an unique id in the board.
                if tile.sc[key] != -1 and tile.sc[key] == tile.color:
                    if key == 'u':
                        dir_map['u'] = (r - 1) * self.max_board + c
                    elif key == 'ur':
                        dir_map['ur'] = (r - 1) * self.max_board + (c + 1)
                    elif key == 'r':
                        dir_map['r'] = r * self.max_board + (c + 1)
                    elif key == 'dr':
                        dir_map['dr'] = (r + 1) * self.max_board + (c + 1)
                    elif key == 'd':
                        dir_map['d'] = (r + 1) * self.max_board + c
                    elif key == 'dl':
                        dir_map['dl'] = (r + 1) * self.max_board + (c - 1)
                    elif key == 'l':
                        dir_map['l'] = r * self.max_board + (c - 1)
                    else:
                        dir_map['ul'] = (r - 1) * self.max_board + (c - 1)
            except KeyError:
                raise Exception("ERROR: No mapping was found for key = " + str(key))

        return dir_map

    # Method that receives two tiles, determines the bounding rectangle and removes the tiles if that's possible,
    # returning the result pair if so
    def remove_adjacent_pairs(self, tile1, tile2, tile_dict):
        # Check if the tiles are diagonally of each other
        r1 = tile1.row
        c1 = tile1.column
        r2 = tile2.row
        c2 = tile2.column
        
        # Lets determine the position of the tiles against each other
        # In this case I can group all possible combinations between two adjacent tiles in three possibilities:
        # Case 1: The tiles are horizontal or vertical of each other:
        if (r1 == r2 and abs(c1 - c2) == 1) or (c1 == c2 and abs(r1 - r2) == 1):
            self.remove_tiles(tile1, tile2, tile_dict)
            return [str(r1) + " " + str(c1) + " " + str(r2) + " " + str(c2)]

        # Case 2: The tiles are diagonally opposed
        elif abs(r1 - r2) == 1 and abs(c1 - c2) == 1:
            # In this case I've determined that the tiles that complete the rest of the square, i.e, the tiles
            # horizontally or vertically adjacent to tile1 and tile2, their ids can be obtained by the formula:
            tile3 = tile_dict[r1 * self.max_board + c2]
            tile4 = tile_dict[r2 * self.max_board + c1]

            # If there's a valid bounding rectangle around
            if tile3.color == tile1.color and tile4.color == tile1.color:
                r3 = tile3.row
                c3 = tile3.column

                r4 = tile4.row
                c4 = tile4.column

                self.remove_tiles(tile1, tile2, tile_dict)
                self.remove_tiles(tile3, tile4, tile_dict)

                return [
                    str(r1) + " " + str(c1) + " " + str(r2) + " " + str(c2),
                    str(r3) + " " + str(c3) + " " + str(r4) + " " + str(c4)
                ]
            else:
                return []
        # Case default: If none of the above conditions are met than the tiles are not adjacent to each other
        else:
            raise Exception("ERROR: The tiles (" + str(r1) + "," + str(c1) + ") and (" + str(r2) + "," + str(c2) + ") are nor adjacent!")

        # I should have my bounding rectangle list by now

        for color in bd:
            # Check if all surrounding tiles have either the same color as one of the tiles or an empty tile instead (-1)
            if color != tile1.color and color != -1:
                # Return false if I detect a different color in the bounding rectangle
                return False

        # If I get to this point, then I'm assuming that I got a valid bounding rectangle. If so:
        return True

    # Method to remove two tiles from the board. To avoid messing too much with the board I'm going to set the color
    # in the removed tiles to -1 (just like an empty cell) and update the surrounding tiles.
    def remove_tiles(self, tile1, tile2, tile_dict):
        if tile1.id not in tile_dict or tile2.id not in tile_dict:
            raise Exception("ERROR: The tiles to remove are already out of the board!")

        # Get the ids from all surrounding tiles of tile1
        sids = self.get_surrounding_ids(tile1)

        # IMPORTANT: The following key list orders all my keys in a sequence that matches with the results from
        # the get_surrounding_ids in a way that the first item on the key_list is the position that I have to
        # set as -1 in the tile pointed by the first position in the surrounding_ids list
        dir_list = [
            'd',
            'dl',
            'l',
            'ul',
            'u',
            'ur',
            'r',
            'dr'
        ]

        if len(sids) != len(dir_list):
            raise Exception("ERROR: Mismatch between the list of keys and surrounding ids. Both lists should have the same size!")

        for i in range(0, len(dir_list)):
            try:
                temp_tile = tile_dict[sids[i]]          # Get a tile from the dictionary
                temp_tile.sc[dir_list[i]] = -1          # And set the direction pointed to tile 1 as empty (-1)

            # For all I know, tile1 can be a corner tile, which means that only has 3 valid surrounding tiles.
            # If I catch a non existent tile (invalid id), I need to protect my code against it
            except KeyError:
                continue

        # Now the same thing to tile2
        sids = self.get_surrounding_ids(tile2)

        if len(sids) != len(dir_list):
            raise Exception("ERROR: Mismatch between the list of keys and surrounding ids. Both lists should have the same size!")

        for i in range(0, len(dir_list)):
            try:
                temp_tile = tile_dict[sids[i]]
                temp_tile.sc[dir_list[i]] = -1
            except KeyError:
                continue

        # Lastly, remove the tiles from the list by setting their color to '-1'. I could "physically" remove the tiles using
        # a del command, but this is easier for debugging purposes
        tile1.color = -1
        tile2.color = -1

    # Method that returns a dictionary with the ids of every tile surrounding the input one
    def get_surrounding_ids(self, tile):
        # So the tile is in a given position given by
        r = tile.row
        c = tile.column

        surrounding_ids = [
            (r - 1) * self.max_board + c,               # up tile
            (r - 1) * self.max_board + (c + 1),         # up-right tile
            r * self.max_board + (c + 1),               # right tile
            (r + 1) * self.max_board + (c + 1),         # down-right tile
            (r + 1) * self.max_board + c,               # down tile
            (r + 1) * self.max_board + (c - 1),         # down-left tile
            r * self.max_board + (c - 1),               # left tile
            (r - 1) * self.max_board + (c - 1)          # up-left tile
        ]

        return surrounding_ids

    # This method receives to horizontally adjacent tiles and returns the corresponding bounding rectangle
    def get_horizontal_bounding_rectangle(self, tile1, tile2):
        # In order to standardize this method I need to order tile1 and tile2 into left_tile and right_tile. The resulting
        # bounding rectangle is the same regardless of the tile positions
        if tile1.column < tile2.column:
            left_tile = tile1
            right_tile = tile2
        elif tile1.column > tile2.column:
            left_tile = tile2
            right_tile = tile1
        else:
            raise Exception("ERROR: The tiles are not horizontally adjacent!")

        # The bounding rectangle is going to be a list with all the colors that surround the smaller rectangle
        # composed by tile1 and tile2
        bd = []

        # And now add all the surrounding colors
        try:
            bd.append(right_tile.sc['u'])
            bd.append(right_tile.sc['ur'])
            bd.append(right_tile.sc['r'])
            bd.append(right_tile.sc['dr'])
            bd.append(right_tile.sc['d'])
            bd.append(left_tile.sc['d'])
            bd.append(left_tile.sc['dl'])
            bd.append(left_tile.sc['l'])
            bd.append(left_tile.sc['ul'])
            bd.append(left_tile.sc['u'])
        except KeyError:
            raise Exception("ERROR: Wrong key-value mapping in horizontal bounding rectangle method.")

        return bd

    # This method receives two vertically adjacent tiles and returns the corresponding bounding rectangle
    def get_vertical_bounding_rectangle(self, tile1, tile2):
        # Same as before: to simplify this function I need to determine which tile is up and which is down
        # NOTE: Since row are filled from top to bottom, the tile with lowest row value is actually on top
        if tile1.row > tile2.row:
            up_tile = tile2
            down_tile = tile1
        elif tile1.row < tile2.row:
            up_tile = tile1
            down_tile = tile2
        else:
            raise Exception("ERROR: The tiles are not vertically adjacent.")

        bd = []

        try:
            bd.append(up_tile.sc['l'])
            bd.append(up_tile.sc['ul'])
            bd.append(up_tile.sc['u'])
            bd.append(up_tile.sc['ur'])
            bd.append(up_tile.sc['r'])
            bd.append(down_tile.sc['r'])
            bd.append(down_tile.sc['dr'])
            bd.append(down_tile.sc['d'])
            bd.append(down_tile.sc['dl'])
            bd.append(down_tile.sc['l'])
        except KeyError:
            raise Exception("ERROR: Wrong key-value mapping in vertical bounding rectangle method.")

        return bd

    # This method receives four tiles in which two of them are diagonally adjacent, calculates the "inner square"
    # formed by the surrounding tiles and returns the resulting, extended bounding rectangle
    def get_diagonal_bounding_rectangle(self, tile1, tile2, tile3, tile4):
        # As with before, I need to determine the order of the tiles. Here's a simple way to do that
        # First add all the tiles to a list (it also works with a dictionary but lists are simpler)
        temp_list = [tile1, tile2, tile3, tile4]

        # Then sort it using the tile id as the sorting key
        sorted_list = sorted(temp_list, key=lambda tile: tile.id, reverse=False)

        # In this situation, the tile with the lowest id value is always the up-right one, followed by the up-left one,
        # then the down-right one and finally the down-right one that has the higher id value because it has the highest
        # row and column values of them all
        up_left_tile = sorted_list[0]
        up_right_tile = sorted_list[1]
        down_left_tile = sorted_list[2]
        down_right_tile = sorted_list[3]

        bd = []

        # The rest is simple and predictable
        try:
            bd.append(up_left_tile.sc['l'])
            bd.append(up_left_tile.sc['ul'])
            bd.append(up_left_tile.sc['u'])

            bd.append(up_right_tile.sc['u'])
            bd.append(up_right_tile.sc['ur'])
            bd.append(up_right_tile.sc['r'])

            bd.append(down_right_tile.sc['r'])
            bd.append(down_right_tile.sc['dr'])
            bd.append(down_right_tile.sc['d'])

            bd.append(down_left_tile.sc['d'])
            bd.append(down_left_tile.sc['dl'])
            bd.append(down_left_tile.sc['l'])
        except KeyError:
            raise Exception("ERROR: Wrong key-value mapping in diagonal bounding rectangle method.")

        return bd

    # Simple method that counts how many colors I have in a given board considering that this info is not directly accessible
    def count_board_colors(self, board):
        colors = [board[0][0]]

        # Scan the board
        for r in range(0, len(board)):
            for c in range(0, len(board[0])):
                if board[r][c] not in colors:
                    # Add any new color to the list if it is not already there
                    colors.append(board[r][c])

        return len(colors)

    # Simple method just to check if the tile color counting is even to all colors
    def check_board_parity(self, board, C):
        color_count = []

        for color in range(0, C):
            color_count.append(0)
            for r in range(0, len(board)):
                color_count[color] += board[r].count(str(color))

        for i in range(0, len(color_count)):
            if color_count[i] % 2 != 0:
                return False

        return True

    # In this method I'm going to create a set of H x W tiles objects, populate them with their respective color
    # and position in the board and fill out the surrounding tiles colors too
    def create_tile_board(self, board):
        # I'm going to save the board into a dictionary
        tile_dict = {}

        # Start by scanning the board
        for r in range(0, len(board)):
            for c in range(0, len(board[0])):
                # Start by creating a tile for the current set of coordinates
                if board[r][c] == 'X':
                    color = -1
                else:
                    color = board[r][c]
                current_tile = SameColorPairs.Tile(r, c, int(color))

                # Case #1: The first tile to be inserted: there's no other tile in place yet so just add it to
                # the dictionary
                if r == 0 and c == 0:
                    # Nothing to do honestly
                    {}

                # Case #2: lets deal with the top row and so I have tiles on my left (and these ones have now
                # something in their right)
                elif r == 0 and c != 0:
                    # Get the left side tile
                    left_tile = tile_dict.get(r * self.max_board + (c - 1))
                    # Update its right tile color
                    left_tile.sc['r'] = current_tile.color
                    # And vice-versa
                    current_tile.sc['l'] = left_tile.color
                # Case #3: Same as above but now dealing along column = 0
                elif r != 0 and c == 0:
                    # Get the tile immediately above
                    up_tile = tile_dict.get((r - 1) * self.max_board + c)
                    upright_tile = tile_dict.get((r - 1) * self.max_board + (c + 1))
                    # Update its bottom color
                    up_tile.sc['d'] = current_tile.color
                    upright_tile.sc['dl'] = current_tile.color

                    current_tile.sc['u'] = up_tile.color
                    current_tile.sc['ur'] = upright_tile.color
                # Case #4: I'm at the last column and I don't have tiles at my up-right and right positions (board limit)
                elif r > 0 and c == len(board[0]) - 1:
                    # Get the tiles
                    up_tile = tile_dict.get((r -1) * self.max_board + c)
                    upleft_tile = tile_dict.get((r - 1) * self.max_board + (c - 1))
                    left_tile = tile_dict.get(r * self.max_board + (c - 1))

                    # Update surrounding colors
                    up_tile.sc['d'] = current_tile.color
                    upleft_tile.sc['dr'] = current_tile.color
                    left_tile.sc['r'] = current_tile.color

                    # Update current tile
                    current_tile.sc['u'] = up_tile.color
                    current_tile.sc['ul'] = upleft_tile.color
                    current_tile.sc['l'] = left_tile.color
                # Case default: this is the most typical situation. With the tiles being placed left to right and top to bottom,
                # any tile that don't fall in the board's extremities has four tiles on its left, up-left, up and up-right positions
                else:
                    # Get the tiles
                    left_tile = tile_dict.get(r * self.max_board + (c - 1))
                    upleft_tile = tile_dict.get((r - 1) * self.max_board + (c - 1))
                    up_tile = tile_dict.get((r - 1) * self.max_board + c)
                    upright_tile = tile_dict.get((r - 1) * self.max_board + (c + 1))

                    # Update the surrounding colors
                    left_tile.sc['r'] = current_tile.color
                    upleft_tile.sc['dr'] = current_tile.color
                    up_tile.sc['d'] = current_tile.color
                    upright_tile.sc['dl'] = current_tile.color

                    # Update colors on current tile too
                    current_tile.sc['l'] = left_tile.color
                    current_tile.sc['ul'] = upleft_tile.color
                    current_tile.sc['u'] = up_tile.color
                    current_tile.sc['ur'] = upright_tile.color

                # Regardless of what has happened before, the last step in each loop run is always the insertion of the
                # current tile in the dictionary
                tile_dict[current_tile.id] = current_tile

        return tile_dict

    # I'm gonna create a specific class to juggle my tiles around
    class Tile(object):
        def __init__(self, r, c, color):
            # Tile position on the board
            self.row = r
            self.column = c
            self.color = color
            # This id field "linearizes" the board by assigning a order number to the tile for easy retrieval from a list
            self.id = r * SameColorPairs.max_board + c

            # In this list I'm going to store the colors of the surrounding tiles (to be filled later on)
            # sc = surrounding_colors
            # IMPORTANT: The list respects the following, non explicit, rule:
            # u = up
            # ur = up right
            # r = right
            # dr = down right
            # d = down
            # dl = down left
            # l = left
            # lu = left up
            # I.e, the first element is the color of the tile immediately above this one and then it goes clockwise from there
            # (-1 if there are no tiles in a certain direction)
            # Example: an upper right tile has its up, up left, left and down left directions as -1 and the remaining ones as
            # an integer
            self.sc = {
                'u': -1,
                'ur': -1,
                'r': -1,
                'dr': -1,
                'd': -1,
                'dl': -1,
                'l': -1,
                'ul': -1
            }

        # This method compares the tile color with every element in the surrounding colors and returns if the tile is valid for
        # removal or not, i.e, returns True if at least one surrounding tile has the same color
        def validate_tile(self):
            if self.color == -1:
                raise Exception("ERROR: The tile has been removed from the board already.")

            for key in self.sc:
                # All I need in one valid surrounding tile
                if self.sc[key] == self.color:
                    return True

            # If I couldn't find it, then this tile has no adjacent same color tiles
            return False

        # This method checks if a tile is islanded, i.e, is surrounded only by empty cells (either the board limits or removed cells)
        def is_island(self):

            if self.color == -1:
                return False

            # Scan all surrounding colors
            for key in self.sc:
                # If there's a non empty tile around it
                if self.sc[key] != -1:
                    return False

            return True

        # This one prints only the basic info of the tile
        def print(self):
            print("Tile id = " + str(self.id))
            print("Position (r, c) = (" + str(self.row) + "," + str(self.column) + ")")
            print("Color = " + str(self.color))

        # Simple method to print out all elements of a tile object
        def printall(self):
            self.print()
            print("Tile surrounding colors: ")
            for key in self.sc:
                print(key, end='')
                print(": " + str(self.sc.get(key)))

    # Method to retrieve a tile from a list by passing its r and c values only. Return None when the tile doesn't exist
    def retrieve_tile(self, r, c, list_of_tiles):
        if not isinstance(list_of_tiles, list):
            raise Exception("ERROR: Invalid list of tiles (not a list!)")

        for tile in list_of_tiles:
            if not isinstance(tile, SameColorPairs.Tile):
                raise Exception("ERROR: Invalid tile in list (not a SameColorPairs.Tile!")

        tile_id = r * self.max_board + c

        if len(list_of_tiles) < tile_id:
            return None
        else:
            return list_of_tiles[tile_id]
