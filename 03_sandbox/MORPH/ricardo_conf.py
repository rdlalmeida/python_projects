import datetime

# Even though this is a purely constant filled document, I have to create a function at this point, in order
# to maintain part of the code flexible and avoid circular references at the same time
# Simple function the returns the current year, in the string format.
# I need it here to update some paths after new year's day. True story...
def get_current_year():
    # Return the first 4 characters of the date string, which is the year value
    return str(datetime.datetime.today())[0:4]

scripts_path = "/home/ricardoalmeida/PycharmProjects/Sandbox/MORPH"
base_util_path = "/home/ricardoalmeida/morph/morph_processing/utils"
input_path = '/home/ricardoalmeida/morph/test_data'
input_archive_path = '/home/ricardoalmeida/morph/test_data_archive'
rinex_path = '/home/ricardoalmeida/morph/rinex_data'
rinex_archive_path = '/home/ricardoalmeida/morph/rinex_archive'
rtk_path = '/home/ricardoalmeida/morph/rtk_data'
rtk_archive_path = '/home/ricardoalmeida/morph/rtk_archive'
zz06_original_path = '/home/ricardoalmeida/morph/leo_files'
zz06_list_of_files = '/home/ricardoalmeida/morph/ZZ06_' + get_current_year() + '_moved_files'
output_path = '/home/ricardoalmeida/morph/movement_records'
bin2std_path = base_util_path + '/bin2std.exe'
runpkr00_path = base_util_path + '/runpkr00'
rnx2rtkp_path = base_util_path + "/rnx2rtkp"
rtk_config = base_util_path + "/morph.conf"

origin = "S5"
end = "S8"

modules = {"H2": ["S5", "S4"],
           "H1": ["ZZ06", "ZZ06"],
           "E2": ["S2", "S1"],
           "E1": ["S3", "S13"],
           "C": ["S9", "S10"],
           "B2": ["S7", "S8"]}

fixed_distances = filter(lambda module: module != ["ZZ06", "ZZ06"], modules.values())
modules_in_order = ["S5", "S4", "ZZ06", "S2", "S1", "S3", "S13", "S9", "S10", "S7", "S8"]

gaps = [["S4", "ZZ06"], ["ZZ06", "S2"], ["S1", "S3"], ["S13", "S9"], ["S10", "S7"], ["S13", "S7"]]

sites = list(set(sum(modules.values(), [])))

useful_distances = [["S13", site] for site in sites]
useful_distances.append([origin, end])

for distance in gaps + fixed_distances:
    if distance not in useful_distances and [distance[1], distance[0]] not in useful_distances:
        useful_distances.append(distance)

for distance in useful_distances:
    if distance[0] == distance[1]:
        useful_distances.remove(distance)

if __name__ == "__main__":
    print "Useful distances ", useful_distances
# These describe the location of the antenna from the center, and nearest end, of each module.
center_offset = {
    'S5': 0,
    'S4': 1866 / 2,
    'S2': 1205,
    'S13': 0,
    'S1': (7670 / 2) - 3200,
    'S3': (7670 / 2) - 3210,
    'S6': 0,
    'S7': -1 * ((7670 / 2) - 1300),
    'S8': -1 * ((7670 / 2) - 1300),
    'S9': 0,
    'S10': 0,
    'ZZ06': 3835
}

length_offset = {
    'S7': -2140,
    'S8': 2140,
    'ZZ06': (19200 / 2) - 1255,
    'S5': -4252,
    'S4': 1140,
    'S2': -3650,
    'S1': 3742,
    'S3': -3742,
    'S13': 2595,
    'S6': 0,
    'S9': -4701,
    'S10': 4701
}

height_offset = {
    'S5': -1870,
    'S4': -1120,
    'S2': -1120,
    'S13': -1120,
    'S1': -1120,
    'S3': -1120,
    'S6': -1120,
    'S7': 0,
    'S8': 0,
    'S9': -220,
    'S10': -220,
    'ZZ06': -1120
}


# These are used to draw the outlines of each module
# They are not critical
module_width = {
    'H2': 10,
    'H1': 10,
    'E2': 10,
    'b': 1.5,
    'E1': 10,
    'A': 13,
    'C': 10,
    'B1': 10,
    'B2': 10
}

module_length = {
    'H2': 19.2,
    'H1': 19.2,
    'E2': 19.2,
    'b': 20,
    'E1': 19.2,
    'A': 28.4,
    'C': 19.2,
    'B1': 19.2,
    'B2': 19.2
}

# This field should exist ONLY when there is no MORPH receivers on the module
approx_loc = {
    'H1': -63.5,
    'b': -25.5,
    'A': 18.7,
    'B1': 62.5
}
