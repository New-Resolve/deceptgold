#!/bin/bash

. $(poetry env info --path)/bin/activate
poetry run pyarmor gen -O src_obf -r -i src/deceptgold
poetry run briefcase build -u
pwd
poetry run briefcase package -v
rm -rf src_obf
rm -rf src/deceptgold.dist-info
echo "================================================================================="
echo "Use the files in the dist directory as a packaged system, ready for distribution."
echo "================================================================================="