#!/bin/sh

if [ $# -lt 1 ]; then
    echo usage $0 branches
    exit 1
fi

BRANCHES=$@

#git remote set-url origin git@github.com:$FORK/odoo.git || exit 1
#git remote set-url upstream git@github.com:odoo/odoo.git || exit 1
git fetch --multiple origin upstream || exit 1

for BRANCH in $BRANCHES ; do
    echo syncing $BRANCH...
    git checkout -B $BRANCH --track origin/$BRANCH || exit 1
    git reset --hard origin/$BRANCH || exit 1
    git pull upstream $BRANCH || exit 1
    git push origin $BRANCH || exit 1
done
