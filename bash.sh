#!/bin/bash
set +o posix
declare -a files
readarray -t files < <( find '/home/music_that_doesnt_even_exist' -type f -name '*.mp3' )
./ui.py "${files[@]}"
