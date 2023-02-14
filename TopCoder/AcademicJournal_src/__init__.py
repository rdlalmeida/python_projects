import AcademicJournal_src.AcademicJournal as acj

papers1 = [
    "A.",
    "B. 0",
    "C. 1 0 3",
    "C. 2"
]

papers2 = [
    "RESPECTED JOURNAL.",
    "MEDIOCRE JOURNAL. 0",
    "LOUSY JOURNAL. 0 1",
    "RESPECTED JOURNAL.",
    "MEDIOCRE JOURNAL. 3",
    "LOUSY JOURNAL. 4 3 3 4",
    "RESPECTED SPECIFIC JOURNAL.",
    "MEDIOCRE SPECIFIC JOURNAL. 6",
    "LOUSY SPECIFIC JOURNAL. 6 7"
]

papers3 = [
    "NO CITATIONS.",
    "COMPLETELY ORIGINAL."
]

papers4 = [
    "CONTEMPORARY PHYSICS. 5 4 6 8 7 1 9",
    "EUROPHYSICS LETTERS. 9",
    "J PHYS CHEM REF D. 5 4 6 8 7 1 9",
    "J PHYS SOC JAPAN. 5 4 6 8 7 1 9",
    "PHYSICAL REVIEW LETTERS. 5 6 8 7 1 9",
    "PHYSICS LETTERS B. 6 8 7 1 9",
    "PHYSICS REPORTS. 8 7 1 9",
    "PHYSICS TODAY. 1 9",
    "REP PROGRESS PHYSICS. 7 1 9",
    "REV MODERN PHYSICS."
]

test1 = {
    "A.",
    "B. 0",
    "C. 1 0 3",
    "C. 2"
}

if __name__ == "__main__":

    aj = acj.AcademicJournal()

    journals = aj.rankByImpact(test1)

    print (journals)