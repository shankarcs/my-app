#!/usr/bin/env bash
licenses_file="$1"
repo_linkname="$2"
set -ex
awk -F',' '{print $1 "," $2 "," $3 "," $4 "," $5 "," $6 "," $7 "'"${repo_linkname}"'" }' intermediate.csv "${licenses_file}"
sed -i 's/"//g' "${licenses_file}"
