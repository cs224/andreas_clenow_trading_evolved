#!/usr/bin/env bash

# exit when any command fails
set -e

echo ">> Updating base environemnt"
conda update -y conda --no-pin
pip install --upgrade pip

echo ">> Setting-up py36zl environemnt"
conda env create -f environment.yml

conda info --envs
