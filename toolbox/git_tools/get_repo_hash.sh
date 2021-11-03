#!/bin/bash
# get_repo_hash.sh
# for an input directory $1
# cat to a file $2 the current commit of the repo
if [ "$#" -ne 2 ]; then
  echo "Usage: $0 /path/to/repo /path/to/outfile" >&2
  exit 1
fi

repo_dir=$1
outfile=$2

cd $repo_dir
commit=`git rev-parse HEAD`
echo "$repo_dir: $commit" >> $outfile

exit 0