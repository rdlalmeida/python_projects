import SameColorPairs_src.SameColorPairs as scp
import SameColorPairs_src.BoardGenerator as bg
import time

board1 = [
    "0434401421",
    "1414440441",
    "1455244342",
    "1223212532",
    "4414423202",
    "5053103402",
    "4433141203",
    "2310031323",
    "3212102431",
    "4045054150"
]

class Test(object):
    def __init__(self, a, b, c):
        self.a = a
        self.b = b
        self.c = c

    def print(self):
        print("a = {0}, b = {1}, c = {2}".format(str(self.a), str(self.b), str(self.c)))

def test_list_dictionary():
    t1 = Test(1, 1, 1)
    t2 = Test(2, 2, 2)
    t3 = Test(3, 3, 3)

    d1 = {'1': t1, '2': t2, '3': t3}
    l1 = [t1, t2, t3]

    print("Dictionary:")
    for key in d1:
        t = d1[key]
        t.print()

    print()
    print("List: ")
    for t in l1:
        t.print()

    print()
    print("Changing t2")

    t2.a = -1

    print("\nDictionary: ")
    for key in d1:
        t = d1.get(key)
        t.print()

    print()
    print("List: ")

    for t in l1:
        t.print()


if __name__ == '__main__':
    H = 100
    W = 100
    C = 6

    generator = bg.BoardGenerator()
    remover = scp.SameColorPairs()

    board = generator.generateBoard(H, W, C)
    #board = board1

    start_time = time.time()

    removal_list = remover.removePairs(board)

    print("--------- %s seconds ---------" % (time.time() - start_time))