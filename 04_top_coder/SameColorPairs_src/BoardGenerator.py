import random

class BoardGenerator(object):
    def generateBoard(self, H, W, C):
        if H < 10 or H > 100:
            raise Exception("ERROR: Invalid Height value: " + str(H) + " (min = 10, max = 100)")

        if W < 10 or W > 100:
            raise Exception("ERROR: Invalid Width value: " + str(W) + " (min = 10, max = 100)")

        if C < 2 or C > 6:
            raise Exception("ERROR: Invalid number of colors: " + str(C) + " (min = 2, max = 6)")

        if H % 2 != 0 and W % 2 != 0:
            raise Exception("ERROR: At least on of the inputs (H or W) needs to be even.")

        board = []

        for row in range(0, H):
            line = ""
            for column in range(0, W):
                # Generate and append to the line string a random numeric value (integer) between 0 and the value of C
                line += str(random.randint(0, C - 1))
            # Add the generated line to the board construct
            board.append(line)

        board = self.equalizeBoard(board, C)

        return board

    def equalizeBoard(self, board, C):
        # Get the initial count for that board
        initial_colors = self.countColors(board, C)

        colors_to_change = []

        for i in range(0, C):
            if initial_colors[i] % 2 != 0:
                colors_to_change.append(i)

        if len(colors_to_change) % 2 != 0:
            raise Exception("ERROR: Wrongly generated board: there are an odd number of odd colored tiles!")

        # If I need to equalize anything
        if len(colors_to_change) > 0:
            random_r = random.randint(0, len(board) - 1)
            random_c = random.randint(0, len(board[0]) - 1)

            while board[random_r][random_c] != str(colors_to_change[0]):
                # Generate random coordinates until a tile that needs change is found
                random_c = random.randint(0, len(board[0]) - 1)
                random_r = random.randint(0, len(board) - 1)

            # Now that I have a valid set of coordinates for a specific value to be changed
            line_to_change = list(board[random_r])
            line_to_change[random_c] = str(colors_to_change[1])
            new_line = ""
            for i in range(0, len(line_to_change)):
                new_line += line_to_change[i]

            board[random_r] = new_line

            # If there are more sets of odd numbered colored tiles, run the algorithm above until achieving a all even board
            if len(colors_to_change) > 2:
                self.equalizeBoard(board, C)

        return board

    def printBoard(self, board):
        if not isinstance(board, list):
            raise Exception("ERROR: Wrong type of input provided (not a list!)")

        for line in board:
            print(line)

        print("\n")

    def countColors(self, board, C):
        colors = []
        for color in range(0, C):
            colors.append(0)
            for line in board:
                for char in line:
                    if str(char) == str(color):
                        colors[color] += 1

        return colors

    def printColors(self, colors, C):
        for i in range(0, C):
            print ("Color #" + str(i) + " = " + str(colors[i]))

    def get_board_from_tile_dict(self, tile_dict):

        board = []
        r = 0
        c = 0
        s = ""

        for key in tile_dict:
            tile = tile_dict[key]

            if tile.row != r and tile.column < c:
                r = tile.row
                c = tile.column

                board.append(s)
                if tile.color == -1:
                    s = 'X'
                else:
                    s = str(tile.color)
            else:
                if tile.color == -1:
                    s += 'X'
                else:
                    s += str(tile.color)
                c = tile.column

        board.append(s)
        return board

    def remove_tiles_from_board(self, results, board):
        if not isinstance(results, list):
            raise Exception("ERROR: Invalid type for results: not a list!")

        for result in results:
            if not isinstance(result, str):
                raise Exception("ERROR: Wrong line type in results: not a str!")

        if not isinstance(board, list):
            raise Exception("ERROR: Wrong type of board: not a list!")

        for line in board:
            if not isinstance(line, str):
                raise Exception("ERROR: Invalid line in board: not a str!")

        for pair in results:
            tokens = pair.split(' ')

            r1 = int(tokens[0])
            c1 = int(tokens[1])
            r2 = int(tokens[2])
            c2 = int(tokens[3])

            for i in range(0, len(board)):
                if r1 == i or r2 == i:
                    line_list = list(board[i])

                    if r1 == i:
                        line_list[c1] = 'X'

                    if r2 == i:
                        line_list[c2] = 'X'

                    board[i] = "".join(line_list)

        return board