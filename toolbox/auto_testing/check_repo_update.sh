#!/bin/bash
# check_repo_update.sh
# check to see if git repo has been updated remotely
# returns exit 0 if no need to compile/test/reinstall
# returns exit 3 if one should compile/test/reinstall
if [ "$#" -ne 2 ]; then
  echo "Usage: $0 /path/to/repo /path/to/hashfile" >&2
  exit 1
fi

MYPATH=`readlink -f "$0"`
MYDIR=`dirname "$MYPATH"`
repo_dir=$1
commits=$2

# do a git pull on the repo
cd $repo_dir
git pull

# check the most recent commit
commit=`git rev-parse HEAD`
echo "$repo_dir: $commit" >> ${commits}.tmp

# compare hashes
diff $commits ${commits}.tmp

if [[ $? == 0 ]]; then
   # no need to recompile/test
   rm -rf ${commits}.tmp
   exit 0
elif [[ $? == 1 ]]; then
   # return with 'error' to compile/test
   rm -rf ${commits}.tmp
   exit 3
fi