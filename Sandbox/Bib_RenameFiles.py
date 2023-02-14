import sys
import os
import pathlib

def renameFiles(path, prefix):
    """ As plain as it seems, this method simply replaces the original file name by the same base file but with a
     different prefix and an new head count based on the number of items in the folder """

    # Start by listing the stuff inside the folder
    file_list = os.listdir(path)
    # And sort it just in case
    file_list.sort();

    data_folder = pathlib.Path(path)

    # Now lets go on a file by file basis
    for i in range(0, len(file_list)):
        
        # If the file in question is this one, i.e., the python script used to change the file names
        if file_list[i][-3:] == ".py":
            # Ignore it. Just move to the next without touching it
            continue

        # I need to remove the original prefix first, so I'm going to split it by the one character that is in all files
        tokens = file_list[i].split("-")
        # Lets now create a dumping ground for all the tokens
        newName = ""

        # The next loop is going to rejoin everyone again apart from the prefix one (hence why the loop starts at 1 and
        # not at 0)
        for j in range(1, len(tokens) - 1):
            # Replace any removed '-' from before
            newName = newName + tokens[j].strip() + "-"

        # And glue on the last element. This has to be done after the loop so that it doesn't get a sticking '-' at the
        # end
        newName = newName + tokens[len(tokens) - 1].strip()

        # Finally, add the specially created new prefix to the file name
        newName = str(getPrefix(i + 1, prefix)) + " - " + newName

        old_file = data_folder / file_list[i]
        new_file = data_folder / newName

        #old_file = file_list[i]
        #new_file = newName

        # And rename the file to the new name
        os.rename(old_file, new_file)

def getPrefix(i, prefix):
    """ This one does a clever thing: it created a somewhat standardised prefix by concatenating a provided prefix
     as an argument and add it a three digit count so that the initial part of the filename always has the same
     length """

    # Start by creating a dumping ground for our stuff
    newPrefix = ""

    # Now the really clever part: I want my head count always within three digit length. To achieve that I'm going to
    # pad enough zeroes on the left side and then complete the three digit format with the actual count. Now, this
    # assumes that no folder has ever more than 999 files (gee, lets really hope that it never gets to that. My
    # supervisor has a bit of an obsession with spending every waking moment reading and analysing articles and nothing
    # more but, but lets just hope that I'm able to do proper scientific research at some point...), so the way I
    # achieve this is by simply checking how many digits the actual count has and then pad the rest
    for j in range(len(str(i)), 3):
        # Add zeroes while you can
        newPrefix = newPrefix + "0"

    # And glue the count afterwards
    newPrefix = str(prefix) + newPrefix + str(i)

    return newPrefix

if __name__ == "__main__":
    #if not os.path.isdir(sys.argv[1]):
    #    raise Exception("ERROR: The path provided " + str(sys.argv[1]) + " is not valid!")

    if len(str(sys.argv[1])) < 1 or len(sys.argv[1]) > 3:
        raise Exception("ERROR: The prefix provided " + str(sys.argv[1]) + " is not valid!")

    path = os.getcwd()
    prefix = sys.argv[1]

    renameFiles(path, prefix)

#    print("Hello! " + str(sys.argv[1]) + " " + str(sys.argv[2]))
