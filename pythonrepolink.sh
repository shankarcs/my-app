#!/usr/bin/env bash
licenses_file="$1"
repo_linkname="$2"
set -ex
awk -F "," '{print $1 "," $2 "," $3 "," $4 "," $5 "," $NF "'"$repo_linkname"'" }' "${licenses_file}"
sed -i 's/"//g' "${licenses_file}"
