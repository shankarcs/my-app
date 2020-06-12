import csv, sys, subprocess, re

inputfile = sys.argv[1]
with open(inputfile, "r") as f, open(".tmp_csv_file", "w") as o:
    csv_reader = csv.reader(f, delimiter=',')
    output = csv.writer(o)
    search_url = "https://search.maven.org/remotecontent?filepath="
    mvn_repo_url = "https://mvnrepository.com/artifact/"
    for row in csv_reader:
        if re.search("com.interset", row[1]) is None:
            # groupid . artifactid . version . artifact-id-version.jar
            group_id = row[1].replace(".", "/")
            artifact_id = row[2].replace(".", "/")
            version = row[3]
            artifact_link = group_id + "/" + artifact_id + "/" + version + "/" + artifact_id + "-" + version + ".jar"
            #download link
            row.append(search_url + artifact_link)
            #homepage link
            row.append(mvn_repo_url + row[1] + "/" + row[2] + "/" + row[3])
            output.writerow(row)
        else:
            row.append("")
            row.append("")
            output.writerow(row)
subprocess.call(['mv', '.tmp_csv_file', inputfile])
