#!/bin/sh --login

datestr=`date +"%Y%m%d"`

source .gitconfig

sed -i -e 's:gituser:${GITHUB_USERNAME}:g' .gitconfig

cp .gitconfig ~/

exit 0
