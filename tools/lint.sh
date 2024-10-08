#!/bin/bash

LINT="pycodestyle"
BRANCH="stage"
EXT="\.py$"

while getopts ":x:b:e:h" opt; do
  case $opt in
    x)
      LINT=$OPTARG
      ;;
    b)
      BRANCH=$OPTARG
      ;;
    e)
      EXT=$OPTARG
      ;;
    h)
      echo -e "Usage: git-diff-lint [options]\n"
      echo "Options:"
      echo -e "  -x\t lint command (default: pycodestyle)"
      echo -e "  -b\t parent branch (default: stage)"
      echo -e "  -e\t file extension regex, (default: .py)"
      echo -e "  -h\t show this help message and exit"
      exit 0
      ;;
    \?)
      echo -e "Invalid option: $OPTARG \ngit-diff-lint -h for help" >&2
      exit 1
      ;;
    :)
      echo -e "Option -$OPTARG requires an argument\ngit-diff-lint -h for help" >&2
      exit 1
      ;;
  esac
done

DIFF=$(git diff --name-only --diff-filter=d $(git merge-base HEAD $BRANCH) | grep $EXT)

if [ -n "$DIFF" ]
then
  ERRORS=$(eval $LINT $DIFF)
  OUT=$?
  if [ $OUT ]
  then
    echo -e "$ERRORS" >&2
  fi
  exit $OUT
else
  exit 0
fi
