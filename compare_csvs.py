import sys, re

old_file = sys.argv[1]
new_file = sys.argv[2]
output_file = sys.argv[3]

with open(old_file, 'r') as t1, open(new_file, 'r') as t2:
    old_csv = t1.readlines()
    new_csv = t2.readlines()

with open(output_file, 'w') as outFile:
    outFile.write("Dependencies Added\n")
    for line in new_csv:
        if re.search("(^interset-|com.interset.)", line) is None:
            if line not in old_csv:
                outFile.write(line)
    outFile.write("Dependencies Removed\n")
    for line in old_csv:
        if re.search("(^interset-|com.interset.)", line) is None:
            if line not in new_csv:
                outFile.write(line)
