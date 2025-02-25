# Main class
class AcademicJournal(object):
    # Main operating method
    def rankByImpact(self, papers):

        # Before anything, the papers variable should come actually as a set (because of using '{}' instead of '[]'
        # So start b converting the input papers to a list
        if isinstance(papers, set):
            papers = list(papers)
            papers.sort()

        if len(papers) < 1 or len(papers) > 50:
            raise Exception("ERROR: Invalid number of papers: " + str(len(papers)) + " (min = 1, max = 50)")

        for paper in papers:
            if len(paper) < 2 or len(paper) > 50:
                raise Exception("ERROR: Invalid number of characters in paper: " + str(len(paper)) + " (min = 2, max = 50)")

            # Start by getting all journals in a nice manipulative structure
            journals = self.get_all_journals(papers)

            # Compute each citations for each journal
            journals = self.calculate_citations_count(journals)

            # And finally, calculate each jornal's ranking
            journals = self.calculate_rankings(journals)

            # I'm finally in a situation where I'm able to organize the journals by ranking, total papers and lexicography
            journals = self.order_journals(journals)

            # I now have my journals properly processed and ordered in my 'journals' variable. Now its just a question of
            # returning a list of strings with the ordered journal names.
            ranked_journal_names = []

            for journal in journals:
                ranked_journal_names.append(journal.name)

            return ranked_journal_names

    # Simple method to order a list of journals according to a set of pre defined rules
    def order_journals(self, journals):
        if not isinstance(journals, list):
            raise Exception("ERROR: Invalid input argument (nor a list!)")

        # Remove a journal from the bottom of the list
        temp_journal = journals.pop()

        # While there's at least one journal in the bundle
        if len(journals) > 1:
            # Call the method recursively
            journals = self.order_journals(journals)

        # It's now time to insert the journal in the list again:
        for i in range(0, len(journals) + 1):
            # Case #1: I'm at the end of the list
            if i == len(journals):
                # Easy, just add it to the end of the list
                journals.append(temp_journal)
                # I'm done. Carry on with the rest of this loop
                return journals
            # Case #2: I have a low ranking journal but I still have plenty of list to go by
            elif temp_journal.ranking < journals[i].ranking:
                # In this case, just forget it and move to the next journal on the list
                continue
            # Case #3: Two entries have the same ranking
            elif temp_journal.ranking == journals[i].ranking:
                # Case #4: I have fewer papers in my temp journal
                if len(temp_journal.own_index) < len(journals[i].own_index):
                    # Same result. Just move over to the next journal. Unless it has also the same ranking, the temp journal is going to get inserted after this one
                    continue
                    # Case #5: Same ranking and same number of papers
                elif len(temp_journal.own_index) == len(journals[i].own_index):
                    # Case #6 (rare): If I detect the same name in different journals
                    if temp_journal.name == journals[i].name:
                        # Raise the proper exception. It shouldn't happen
                        raise Exception("ERROR: Multiple copies of journal " + str(temp_journal.name) + " detected.")
                    # Case #7: Same ranking, same number of papers but in the wrong alphabetic order. Carry on as usual. Go to the next journal and this one should be inserted
                    # between journals[i] and journals[i + 1]
                    elif temp_journal.name > journals[i].name:
                        continue
                    else:
                        return self.insert_journal_at_index(temp_journal, journals, i)
                else:
                    return self.insert_journal_at_index(temp_journal, journals, i)
            else:
                return self.insert_journal_at_index(temp_journal, journals, i)

    # This method inserts a journal into a list of journals just before a given index
    def insert_journal_at_index(self, journal, journals, index):
        if not isinstance(journal, AcademicJournal.Journal):
            raise Exception("ERROR: Invalid journal entry (Not a Journal!)")

        if not isinstance(journals, list):
            raise Exception("ERROR: Invalid list of journals (Not a list)")

        if index >= len(journals):
            raise Exception("ERROR: Invalid insert position. Its over the list limits!")

        # If all inputs are OK, then the rest is simple:
        # Copy the bit of the list before the inserting point
        temp_journals = journals[0:index]
        # Append the journal to the end of the semi list
        temp_journals.append(journal)

        # And collate the rest of the list
        for i in range(index, len(journals)):
            temp_journals.append(journals[i])

        return temp_journals

    # To make things easier, I'm going to use a specific class for each journal
    class Journal(object):
        # Here goes the number of times that this paper is cited by another
        citation_count = 0
        # And the final ranking
        ranking = 0

        def __init__(self, name, citations, own_index):
            if not isinstance(name, str):
                raise Exception("ERROR: Invalid journal name supplied: " + str(name))

            if not isinstance(citations, list):
                raise Exception("ERROR: Invalid list of indexes supplied (not a list)")

            self.name = name.upper()
            self.citations = []

            # Remove any duplicates from citations (lazy authors and/or editors that allow multiple citations to the same paper in the same paper)
            if len(citations) > 0:
                citations = self.remove_duplicates(citations)

            for citation in citations:
                self.citations.append(citation)

            self.own_index = []
            self.own_index.append(own_index)

        # Simple method to remove duplicate elements from a list recursively
        def remove_duplicates(self, list_of_stuff):
            if not isinstance(list_of_stuff, list):
                raise Exception("ERROR: The input argument is not a list!")

            # Get the first (or last) element of a list into memory
            temp = list_of_stuff.pop()

            # As long as there are more than one element in the list, just call this function over and over again
            if len(list_of_stuff) > 1:
                self.remove_duplicates(list_of_stuff)

            # At this point I should have the list of stuff with only one element in it... and another element in the temp variable
            if temp not in list_of_stuff:
                # Return an element to the list only if it is unique
                list_of_stuff.append(temp)
            return list_of_stuff

        # This method adds a new index, i.e, another position in the papers list where this journal appears
        def add_own_index(self, index):
            if not isinstance(index, int):
                raise Exception("ERROR: Provided index value is not an integer: " + str(index))

            if not int(index) in self.own_index:
                # Add a new index if the provided value is not already in the list
                self.own_index.append(index)
            else:
                raise Exception("ERROR: Duplicate indexes!")

        # And this one calculates the journal rating (after all calculations are done)
        def calculate_rating(self):
            # Easy: the ranking is the quocient between the number of times this journal was cited by other papers and the number of papers from this journal in the papers variable
            self.ranking = self.citation_count/len(self.indexes)

        # This method adds new citations to an already existing journal
        def add_citations(self, citation_list):
            if not isinstance(citation_list, list):
                raise Exception("ERROR: Invalid input citation list (not a list!)")

            if len(citation_list) > 0:
                citation_list = self.remove_duplicates(citation_list)

            for citation in citation_list:
                try:
                    self.citations.append(int(citation))
                except ValueError:
                    raise Exception("ERROR: Invalid citation format: " + str(citation) + " (Not an int!)")

    # This method does the thing, i.e, computes the total citations by analysing each journal entry and the info present there
    # NOTE: Call this method only after running the create_journal one
    def calculate_citations_count(self, journals):
        if not isinstance(journals, list):
            raise Exception("ERROR: The input element is from the wrong type (not a list!)")

        # Cool. Carry on with the computation
        for i in range(0, len(journals)):
            if not isinstance(journals[i], AcademicJournal.Journal):
                raise Exception("ERROR: The journal in index " + str(i) + " is from a wrong type (not a Journal).")

            # Lets start by picking up a journal:
            current_journal = journals[i]

            # And now check every other journal on the list for citations matching this one's indexes
            for j in range(0, len(current_journal.own_index)):
                for k in range(0, len(journals)):
                    if journals[k].name == current_journal.name:
                        # I don't what to count self citations. As so I'm jumping over these cases
                        continue
                    else:
                        # Otherwise just go through each one of the other journals and count how many indexes of this one are in the citation array.
                        current_journal.citation_count = current_journal.citation_count + journals[k].citations.count(current_journal.own_index[j])

            # Update the journal reference
            journals[i] = current_journal
        return journals

    # And this one calculates the ranking according to the provided rules
    # NOTE: Again, only works if the citation count is already done
    def calculate_rankings(self, journals):
        if not isinstance(journals, list):
            raise Exception("ERROR: Invalid type of input argument (not a list!)")

        for i in range(0, len(journals)):
            if not isinstance(journals[i], AcademicJournal.Journal):
                raise Exception("ERROR: Entry #" + str(i) + " of journals is not a Journal!")

            journals[i].ranking = journals[i].citation_count/len(journals[i].own_index)

        return journals

    # Lets start with a method that receives a set of papers and returns a list of journal objects
    def get_all_journals(self, papers):
        if not isinstance(papers, list):
            raise Exception("ERROR: Invalid input papers! (not a list)")
        journals = []
        acdj = AcademicJournal()

        for i in range(0, len(papers)):
            if i < 0 or i > len(papers):
                raise Exception("ERROR: The index is over the existing number of papers.")
            # Go through each paper and update or add entries to the journal list
            journals = acdj.create_journal(papers[i], i, journals)

        return journals

    # I need a method just to check if all entries from "papers" are valid, i.e, they respect the pre-established format and returns a Journal object with all that information
    def create_journal(self, paper, paper_index, journals):
        if not isinstance(paper, str):
            raise Exception("ERROR: The paper provided " + str(paper) + " is not a string.")

        if not isinstance(paper_index, int):
            raise Exception("ERROR: Invalid paper index. Not an integer: " + str(paper_index))

        if not isinstance(journals, list):
            raise Exception("ERROR: The list of journals provided is not an list")

        for journal in journals:
            if not isinstance(journal, AcademicJournal.Journal):
                raise Exception("ERROR: Not all elements in journals are valid elements!")

        # Start by splitting the string by the "." which I know it exists in it
        tokens = paper.split('.')

        # I expect at least 2 tokens: one with just the name and another with the citations list (that may as well be an empty string but it always gets a len(tokens) >= 2)
        if len(tokens) < 2:
            raise Exception("ERROR: Wrong paper format!")

        # The name is easy: its the first token capitalized
        journal_name = str(tokens[0]).upper()

        # The list of citations comes from the second token, which at this point is still a list of strings
        citation_list = tokens[1].strip().split(' ')
        cit_int_list = []

        # Add more citations to the list if there are any to begin with
        if citation_list[0] != '':
            # Convert all citations into integers and add them to a special list
            for citation in citation_list:
                try:
                    cit_int_list.append(int(citation))
                    if int(citation) == paper_index:
                        raise Exception("ERROR: The paper cites himself (not an euphemism!)")

                except ValueError:
                    raise Exception("ERROR: Citation from journal " + str(journal_name) + ": " + str(citation) + " is not in a correct format (int)")

        # I need to check if the journal list is empty to start with. If so
        if len(journals) == 0:
            # Create and populate a journal object with the provided data
            j1 = AcademicJournal.Journal(journal_name, cit_int_list, paper_index)
            # And add it to the journal list
            journals.append(j1)
        else:
            # Set a simple flag
            found_journal = False

            # Before going any further, I now need to check if the given journal exists already (check the name)
            for journal in journals:
                # If the given journal already exists
                if journal.name == journal_name:
                    # Add the new citation list to it
                    journal.add_citations(cit_int_list)
                    # And add a new index to the list of self appearances
                    journal.add_own_index(paper_index)
                    # Set the flag signaling that an update has already been made
                    found_journal = True

                    # Each journal should only have one entry. If I found it, then I can terminate this loop
                    break

            # If I didn't find an existing entry
            if not found_journal:
                # Create the Journal entry
                j1 = AcademicJournal.Journal(journal_name, cit_int_list, paper_index)

                # And finally add the new entry to the existing list
                journals.append(j1)

        # Send back the updated journal list
        return journals




    # Simple method to print a Journal object
    def print_journal(self, journal):
        if not isinstance(journal, AcademicJournal.Journal):
            raise Exception("ERROR: The journal provided is not in the right format.")

        print("Journal name: " + str(journal.name))
        print("List of citations: ", end='')
        print(journal.citations)
        print("Index list: ", end='')
        print(journal.own_index)
        print("Citation count: " + str(journal.citation_count))
        print("Ranking: " + str(journal.ranking))