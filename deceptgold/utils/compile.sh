#!/bin/bash

. $(poetry env info --path)/bin/activate
poetry run pyarmor gen -O src_obf -r -i src/deceptgold
poetry run briefcase build -u
poetry run briefcase package
rm -rf ../src_obf