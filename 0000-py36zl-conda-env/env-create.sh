#!/usr/bin/env bash

# exit when any command fails
set -e

echo ">> Updating base environemnt"
conda update -y conda --no-pin
conda install mamba -n base -c conda-forge
pip install --upgrade pip

echo ">> Setting-up py36zl environemnt"
mamba env create -f environment.yml

conda info --envs
