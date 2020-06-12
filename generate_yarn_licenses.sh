#!/usr/bin/env bash
set -e
yarn_files="$(find . -name yarn.lock)"
package_json_files="$(find . -name package.json)"
for j in $(echo $package_json_files|xargs); do
    pushd "$(dirname $j)"
    yarn remove interset-ui --non-interactive || true
    yarn remove interset-utils --non-interactive || true
    yarn remove interset-api --non-interactive|| true
    yarn remove dashboard --non-interactive || true
    popd
done

i=1
for file in $(echo $yarn_files|xargs); do
    yarn licenses list --json --no-progress --non-interactive --prod --cwd "$file" |  jq '. | select(.type | contains("table"))' >> automation_licenses_"$i".json
    i=$(( i + 1))
done
