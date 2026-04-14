#!/bin/bash
## Copyright (C) 2012-2019 Continental Automotive Systems, Inc.
## script to generate info for tickets included since last baseline.

repo_header()
{
	printf '%*s\n' "80" ' ' | tr ' ' "="
	echo -e "Repo: $REPO_PROJECT ${1}\n"
}

[ $# != 3 -o -z "$REPO_PROJECT" -o -z "$REPO_REMOTE" ] && exit -1

echo "checking for $REPO_PROJECT ..."
## look for previous revision: filter based on projet and path
prev_rev=`grep \"$REPO_PROJECT\" $1 | grep \"$REPO_PATH\" \
	| sed -e 's#.*revision="##' \
	| sed -e "s#\".*##" 2>/dev/null`

#echo "$REPO_PROJECT revision: $prev_rev $REPO_LREV"
[ "$prev_rev" = "$REPO_LREV" ] && exit 0

h=""
[ -z "$prev_rev" ] && h="(Added)"

repo_header ${h} >> $2
repo_header ${h} >> $3

[ -z "$prev_rev" ] && exit 0

git log ${prev_rev}..${REPO_LREV} >> $2

# WORKAROUND: Change report ready for CVS format.
git log ${prev_rev}..${REPO_LREV} --pretty=format:"%h | %an | %ad | %s" --date=short >> $3

echo >> $2
echo >> $3
