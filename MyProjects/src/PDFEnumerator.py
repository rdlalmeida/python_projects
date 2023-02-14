import os


class PDFEnumerator(object):
    def __init__(self):
        self.working_folder = os.getcwd()

    # Method that list and sorts the pdf files found in the working folder. The method is able to detect if there is an already defined order (numerical)
    # and continues it if possible. Otherwise it reorders everything from 0.
    def order_pdf_files(self):
        if not os.path.isdir(self.working_folder):
            raise Exception("ERROR: Invalid working folder: " + str(self.working_folder))

        # First retrieve all .pdf files in the current working folder
        pdf_files = filter(lambda file: file[-4:] == ".pdf", os.listdir(self.working_folder))

        # Now I'm going to split all my files into ordered and not ordered
        unordered_files = []
        ordered_files = []

        # And I'm storing the highest ordering number in this variable
        highest_order = -1

        # All my ordered files are going to be named as "Order_number - File_name.pdf", ergo, by splitting the name by the '-' character I should
        # get either if a file is ordered and what is its order number
        for pdf_file in pdf_files:
            # Start by splitting the file name by the dash character to split order numbers from the rest of the text
            tokens = pdf_file.split("-")

            # To separate the ordered files from the rest, I'm going to try and cast the first element of the split (tokens[0]) into an integer.
            try:
                # If the operation is OK, than the file is ordered and I can proceed normally
                order_number = int(tokens[0])
                ordered_files.append(pdf_file)

                if order_number > highest_order:
                    highest_order = order_number
            # If not, I'm going to catch that exception (since in this particular case is not an error per se) and deal with the unordered file.
            except ValueError:
                unordered_files.append(pdf_file)

        # I should now have two lists with ordered and unordered files. Lets do a quick error check just in case
        if len(ordered_files) > 0 and highest_order == -1:
            raise Exception("ERROR: Missing something since highest order wasn't updated and there are files in the ordered list.")

        # The next section should only run if there are unordered files. Otherwise just finish the script
        if len(unordered_files) > 0:
            if highest_order == -1:
                # If no ordered files were detected so far, reset this variable since I'm going to use it to rename the files
                order = 1
            else:
                # Otherwise start the numbering after the last numbered file
                order = highest_order + 1

            for unordered_file in unordered_files:
                new_name = str(order) + " - " + str(unordered_file)
                os.rename(os.path.join(self.working_folder, unordered_file), os.path.join(self.working_folder, new_name))
                order = order + 1
