#!/usr/bin/env bash

# exit when any command fails
set -e

echo ">> Setting-up py36zl environemnt"
mamba env create -f environment.yml

conda info --envs
