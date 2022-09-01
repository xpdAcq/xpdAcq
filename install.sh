#!/bin/bash

set -e
env="$1"
conda create -n "$env" --yes
conda install -n "$env" -c conda-forge --file requirements/build.txt \
--file requirements/run.txt \
--file requirements/test.txt \
--file requirements/docs.txt \
--yes
conda run --live-stream --no-capture-output -n "$env" pip install -e . --no-deps
echo "Package has been successfully installed."
echo "Please run the following command to activate the environment."
echo ""
echo "    conda activate $env"
echo ""
