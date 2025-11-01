import sys

def sayHello():
    print("Hello Mr. Bad Luck!")

def printSysVars():
    print("sys.prefix = ", sys.prefix)
    print("sys.exec_prefix = ", sys.exec_prefix)
    print("sys.base_prefix = ", sys.base_prefix)
    print("sys.base_exec_prefix = ", sys.base_exec_prefix)


if __name__ == "__main__":
    printSysVars()