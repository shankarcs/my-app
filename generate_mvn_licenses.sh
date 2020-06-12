#!/usr/bin/env bash
licenses_file="$1"
set -ex
mvn license:aggregate-download-licenses
xml2csv --input target/generated-resources/licenses.xml --noheader --output intermediate.csv --tag="dependency" --ignore="comments"
awk -F',' '{ print $4 "," $1 "," $2 "," $3 }' intermediate.csv | sort -u  >> "${licenses_file}"
sed -i 's/"//g' "${licenses_file}"
