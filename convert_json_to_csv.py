import csv, json, sys, subprocess, re

inputfile = sys.argv[1]
outputfile = sys.argv[2]
with open(inputfile, "r") as f, open(outputfile, "a") as o:
    data = json.load(f)
    data["data"]["body"].sort(key=lambda x:x[2])
    license_first_order = [2,0,1,3,4,5]
    output = csv.writer(o)
    for row in data["data"]["body"]:
        if re.search("(interset|workspace-aggregator)", row[0]) is None:
            row = [row[i].encode('utf-8') for i in license_first_order]
            package_name = row[1] + '@' + row[2]
            # appending link to download
            row.append(subprocess.check_output(["npm", "v", package_name, "dist.tarball"]).encode('utf-8').rstrip())
            # appending link to homepage
            homepage_link = "https://www.npmjs.com/package/" + row[1] + "/v/" + row[2]
            row.append(homepage_link)
            output.writerow(row)
        else:
            row.append("")
            row.append("")
            output.writerow(row)
