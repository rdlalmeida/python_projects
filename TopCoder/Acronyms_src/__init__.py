import Acronyms_src.Acronyms as acrms

example1 = ["We the people of the United States of America"]

example2 = [
    "Don't",
    "worry.",
    "Be",
    "Happy!"
]

example3 = [
    "Entering contests at TopCoder, Inc.",
    "is a good way to develop your skills."
]

example4 = [
    "Working at the United States Postal Service",
    "in the United States of America",
    "is a satisfying experience."
]

example5 = ["a A & a & a B"]

example6 = [
 "The First word can't be included. In",
    "A sequence, that is."
]

example7 = ["A Test & Test & & TEst"]

example8 = [
    "This is a TEST tEST Test. ",
    ".Go Test"
]


if __name__ == '__main__':
    acronym = acrms.Acronyms()

    #sentence = acronym.acronize(example8)

    #print (sentence)

    #exit(0)

    examples = [
        example1,
        example2,
        example3,
        example4,
        example5,
        example6,
        example7,
        example8
    ]

    for i in range(0, len(examples)):
        sentence = acronym.acronize(examples[i])
        print (sentence)
