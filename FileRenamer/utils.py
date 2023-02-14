# In this script I'm going to keep all functions that I want to use in the main scrips. Compartmentalize baby!


# Method to print out the contents of a read file
def print_file_contents(file_descriptor):
    # Read a line from the file and remove the traditional newline in the end
    line = file_descriptor.readline().strip("\n")
    while line != "":
        print (line)
        line = file_descriptor.readline().strip("\n")


# Method that receives a text data base and return a list with all the words in it
# Note: the method is blind to the file content. Each element of the list is a line of the file
def get_words_to_remove_database(file_descriptor):
    list_to_return = []

    line = file_descriptor.readline().strip("\n")

    while line != "":
        list_to_return.append(line)
        line = file_descriptor.readline().strip("\n")

    return list_to_return


# Simple function to escape a couple of Linux troublesome characters so that the os.system calls can be made.
def escape_filename(old_filename):
    if len(old_filename) <= 0:
        raise Exception("ERROR: Invalid filename provided: " + str(old_filename))

    new_filename = old_filename.replace(' ', '\ ')
    new_filename = new_filename.replace('(', '\(')
    new_filename = new_filename.replace(')', '\)')
    new_filename = new_filename.replace("'", "\\'")
    return new_filename
