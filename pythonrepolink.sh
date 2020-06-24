#!/usr/bin/env bash
licenses_file="$1"
repo_linkname="$2"
repo_dependency="$3"
set -ex
awk -F "," '{print $1 "," $2 "," $3 "," $4 "," $5 "," $6 "'"$repo_linkname"'" }' "${licenses_file}" | sort -u  >> "${repo_dependency}"
sed -i 's/"//g' "${repo_dependency}"
