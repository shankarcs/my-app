#!/usr/bin/env bash
licenses_file="$1"
repo_linkname="$2"
set -ex
echo "${repo_linkname}"
pip-licenses --with-system --with-authors --with-urls --format=csv --output-file=python_license.csv
awk -F',' '{ print $1 "," $2 "," $3 "," $4 "," $5} BEGIN { OFS = "," } {$6="${repo_linkname}"; print}' python_license.csv | sort -u  >> "${licenses_file}"
sed -i 's/"//g' "${licenses_file}"
