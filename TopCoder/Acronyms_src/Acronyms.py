class Acronyms(object):

    def acronize(self, document):
        # Lets do all validations at this point
        # Start by checking if document is indeed passed as a list
        if not isinstance(document, list):
            raise Exception("ERROR: The provided input has the wrong type (not a list!)")

        # Check if the number of elements in document is between 1 and 50
        if len(document) < 1 or len(document) > 50:
            raise Exception("ERROR: Invalid number of elements in document: " + str(len(document)))

        for i in range(0, len(document)):
            # Check if all elements in document are indeed strings
            if not isinstance(document[i], str):
                raise Exception("ERROR: Invalid document member format! (Not a string): " + str(document[i]))

            # Check if all elements in document have between 1 and 50 characters
            if len(document[i]) < 1 or len(document[i]) > 50:
                raise Exception("ERROR: Wrong number of characters in sentence (min = 1, max = 50): " + str(len(document[i])))

            # Before going any further, check if the current document has at least two upper case words in it
            if self.count_upper_case_words(document) < 2:
                raise Exception("ERROR: The document provided has less than two upper cased words in it!")

            # Transform the string into a list for ease of manipulation
            sentence_list = list(document[i])

            # Check if any elements in document has a leading space
            if sentence_list[0] == ' ':
                raise Exception("ERROR: The element " + str(document[i]) + " begins with a leading space!")

            # Check if any of the elements in document has more than one trailing spaces
            if sentence_list[-1] == ' ' and sentence_list[-2] == ' ':
                raise Exception("ERROR: The element " + str(document[i]) + " has more than one trailing spaces")

            # Check if the last element in document does not have any trailing spaces
            if i == len(document) - 1 and sentence_list[-1] == ' ':
                raise Exception("ERROR: The last element in the document has a trailing space: " + str(document[i]))

            # Go through all characters in each element
            for j in range(0, len(sentence_list)):
                # And check if they are within the desired ASCII range
                if ord(sentence_list[j]) < 32 or ord(sentence_list[j]) > 122:
                    raise Exception("ERROR: Character " + str(sentence_list[j]) + " is out of the ASCII range!")

                # In this one I'm checking for consecutive non-letter characters that are not spaces
                if j != 0 and not sentence_list[j].isalpha() and not sentence_list[j - 1].isalpha() \
                        and sentence_list[j] != ' ' and sentence_list[j - 1] != ' ':
                    raise Exception("ERROR: Detected two consecutive non letter characters: " + str(sentence_list[j - 1]) + " and "
                                    + str(sentence_list[j]) + " in " + str(document[i]))

                # And finally check for consecutive space characters in all elements
                if j != 0 and sentence_list[j - 1] == ' ' and sentence_list[j] == ' ':
                    raise Exception("ERROR: Consecutive spaces detected in " + str(document[i]) + " at " + str(j - 1) + " and " + str(j) + " positions.")

        sentence = Acronyms.Sentence(document)
        # Before going any further, process any acronyms in this sentence already
        sentence.process_acronyms()

        final_sentence = ""
        # I'm finally in a position to rebuild the sentence replacing every valid uppercased word by its acronym
        # I'm going to simply loop by as many words as I ever counted for that document (this value was stored in self.total_words) and check if,
        # for a given index, I have a corresponding words somewhere in either the acronym or non_acronym sets (or none as it may also happen at this point)
        for i in range (0, sentence.total_words):
            if i in sentence.acronym_indexes:
                # NOTE: I need to resolve the index first. By splitting all words into two groups and fusing some of them into a single word (acronym)
                # wreaked havok among my internal indexes (the internal indexes no longer match the positional ones). As such I need to be extra careful in
                # this step
                index = sentence.acronym_indexes.index(i)

                # Add the word to the sentence with a white space as terminator for now
                final_sentence += sentence.acronym_words[index]
            elif i in sentence.non_acronym_indexes:
                index = sentence.non_acronym_indexes.index(i)
                final_sentence += sentence.non_acronym_words[index]

            # Check if the current final sentence has a trailing white space
            if final_sentence[-1] != ' ':
                # And add it if not
                final_sentence += ' '

        # Remove any trailing spaces from the final result
        final_sentence =  final_sentence.strip()

        # And return the final result!
        return final_sentence

    # Method to count how many upper cased words are in a document, i.e, the total of uppercase words in a set of elements
    def count_upper_case_words(self, document):
        # Lets start by joining all elements into a nice little sentence
        upper_cased_words = 0
        for i in range(0, len(document)):
            # Start by splitting the document element by its white spaces
            tokens = document[i].split(" ")

            # And the join them all up
            for j in range(0, len(tokens)):
                if tokens[j].istitle():
                    # When a upper case word is found, add one to the count
                    upper_cased_words = upper_cased_words + 1

        return upper_cased_words

    class Sentence(object):
        def __init__(self, document):
            self.acronym_words = []
            self.acronym_indexes = []
            self.non_acronym_words = []
            self.non_acronym_indexes = []

            self.total_words = 0

            for i in range(0, len(document)):
                words = document[i].split(' ')

                for j in range(0, len(words)):
                    # First one is easy: the first word of the document is never part of an acronym
                    # If I'm over the first word and the last one ended with a '.' then I'm in a new sentence and the first word in it is out of any acronym
                    if (i == 0 and j == 0) or (j > 0 and words[j - 1][-1] == '.') or words[j][0] == '.':
                        # Add the word and its index to the proper structure
                        self.non_acronym_indexes.append(self.total_words)
                        self.non_acronym_words.append(words[j])
                        self.total_words += 1
                        continue

                    # Those above were special cases. From now on, capitalized words go into the potential acronym list and
                    # lower case ones go to the non acronym one
                    if self.istitle(words[j]):
                        self.acronym_indexes.append(self.total_words)
                        self.acronym_words.append(words[j])
                        self.total_words += 1
                        continue

                    else:
                        self.non_acronym_indexes.append(self.total_words)
                        self.non_acronym_words.append(words[j])
                        self.total_words += 1
                        continue

                    # Up to here, each word insertion is followed by a 'continue' instruction, which means that I should never reach
                    # this point in the code if all my 'if' conditions are able to encase all possible word combinations.
                    # I'm gonna raise an exception after this point just as a debug flag than anything else, to catch any unforeseen cases.
                    raise Exception("ERROR: The word " + str(words[i]) + " at position " + str(i) + " does not found any place for itself!")

        # This method processes the acronyms in a sentence object, i.e, replaces all elements in the sentence.acronym_words by their respective acronyms
        def process_acronyms(self):
            if len(self.acronym_words) < 2:
                raise Exception("ERROR: Not enough acronym words in this sentence.")

            # Control index
            index = 1
            # I'm going to build my temporary acronyms here. Fill it in with the fist letters of the acronym
            temp_acronym = [self.acronym_words[0][0]]

            for i in range(1, len(self.acronym_words[0])):
                if self.acronym_words[0][i].isupper():
                    # Check for additional upper case characters in the word
                    temp_acronym.append(self.acronym_words[0][i])

            total_acronyms = []

            # The new acronized words are going to retain the index of the first word of the acronym. I can preemptively fill in the first
            total_indexes = [self.acronym_indexes[0]]

            # Any word between two upper case words is going to disappear. I'm going to save their indexes here
            indexes_to_remove = []

            # And take note of how many words are in the current acronym
            acronym_count = 1

            # Lets roll through all acronym words gathered so far
            while index < len(self.acronym_words):
                # If the two words are next to each other
                if self.acronym_indexes[index] - self.acronym_indexes[index - 1] == 1:
                    # Add another letter to the running acronym
                    temp_acronym.append(self.acronym_words[index][0])
                    # Increment the word count
                    acronym_count = acronym_count + 1

                    # And any additional upper case letters along the way
                    for k in range(1, len(self.acronym_words[index])):
                        if self.acronym_words[index][k].isupper():
                            temp_acronym.append(self.acronym_words[index][k])

                # If the words only have another word between them
                elif self.acronym_indexes[index] - self.acronym_indexes[index - 1] == 2:
                    # Add the letter to the building acronym as well
                    temp_acronym.append(self.acronym_words[index][0])
                    acronym_count = acronym_count + 1

                    for k in range(1, len(self.acronym_words[index])):
                        if self.acronym_words[index][k].isupper():
                            temp_acronym.append(self.acronym_words[index][k])

                    # And signal the in-between word for removal
                    indexes_to_remove.append(self.acronym_indexes[index] - 1)
                # Last possible option: the current acronym is done. Move to the next if possible
                else:
                    # If I get here, either I have a fully formed acronym in temp_acronym at this point or I have a single upper cased word
                    # somewhere in the middle of the sentence. If that's the case I shouldn't make any acronyms out of it
                    if acronym_count <= 1:
                        # Add the non acronized word as is to the acronym list, as if it was an acronym. (Doesn't really matter at this point)
                        temp_acronym = list(self.acronym_words[index - 1])

                    # Here's a tricky bit. If the last character of the last word of the acronym has a non letter character (such as '.' or '!'), I have
                    # to retain it. Its not that difficult to check once I started my loop from position #2
                    elif not self.acronym_words[index - 1][-1].isalpha():
                        # If I detect that character is not a letter, add it to the acronym too
                        temp_acronym.append(self.acronym_words[index - 1][-1])

                    total_acronyms.append("".join(temp_acronym))
                    # Add the current word's index to the total since the new acronym is going to have this index
                    total_indexes.append(self.acronym_indexes[index])
                    # And save the fist letter into the temporary acronym
                    temp_acronym = [self.acronym_words[index][0]]
                    # Reset the counter too
                    acronym_count = 1

                # Increment the index after each loop
                index = index + 1

            # At this point I'm out of the while loop but I still have some house cleaning to do
            if acronym_count <= 1:
                temp_acronym = list(self.acronym_words[index - 1])
            elif not self.acronym_words[index - 1][-1].isalpha():
                temp_acronym.append(self.acronym_words[index - 1][-1])

            total_acronyms.append("".join(temp_acronym))

            # Finally, remove any words from the non_acronym list and replace all acronym words for the acronyms themselves
            # Begin by removing any inbetween words from the non acronym list
            if len(indexes_to_remove) > 0:
                for i in range(0, len(indexes_to_remove)):
                    index = self.non_acronym_indexes.index(indexes_to_remove[i])
                    del self.non_acronym_words[index]
                    del self.non_acronym_indexes[index]

            # Finally replace this sentence's acronym words and indexes by the actual processed acronyms and indexes
            self.acronym_words = total_acronyms
            self.acronym_indexes = total_indexes


        # This method overloads the str.istitle() built in method of sorts. The str.istitle() method results true only if the first character of a
        # string (or word) is upper case and nothing else. If a word as multiple uppercase characters in it (as for instance TopCoder), the method
        # returns false, which is wrong in this case. As such I need to redefine a similar method to overcome this issue
        def istitle(self, word):
            if not isinstance(word, str):
                raise Exception("ERROR: The word provided is not a string!")

            # This is as simple as it gets: if the first character of the word is an upper case one, return True. Otherwise return False.
            return word[0].isupper()


        # Standard printing method for Sentence class objects
        def print_sentence(self):
            if len(self.acronym_indexes) != len(self.acronym_words) or len(self.non_acronym_words) != len(self.non_acronym_indexes):
                raise Exception("ERROR: Mismatch between indexes and word counts!")

            print("Acronym words = " + str(len(self.acronym_words)) + ":")
            for i in range(0, len(self.acronym_words)):
                print(str(self.acronym_words[i]) + "@[" + str(self.acronym_indexes[i]) + "]")

            print("\nNon acronym words = " + str(len(self.non_acronym_words)) + ":")
            for i in range(0, len(self.non_acronym_words)):
                print(str(self.non_acronym_words[i]) + "@[" + str(self.non_acronym_indexes[i]) + "]")


        # Method that joins all elements together in a single sentence, decides if there are elements that need spaces in between them (if one of
        # them ends with a '.') and then tokenize the whole thing and returns the list with all the document's words in order
        def tokenize_document(self, document):
            # Since all possible validations where already made before (in the entry point method: acronize) I'm gonna go and assume that
            # all input data from this point on is valid
            sentence = []
            for i in range(0, len(document)):
                # Get all words from that particular element
                tokens = document[i].strip().split(' ')

                # Then finally add all it up in one list and return it back
                for j in range(0, len(tokens)):
                    tokens[j].strip()
                    sentence.append(tokens[j])

            return sentence