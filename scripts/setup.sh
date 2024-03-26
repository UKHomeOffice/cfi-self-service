#!/bin/bash

# Make a virtual environment workspace:
export VENV=~/env
python3 -m venv $VENV

# Wire your shell to use the virtual environment:
$VENV/bin/activate

# Update packaging tools in the virtual environment:
$VENV/bin/pip install --upgrade pip setuptools

# Install pyramid and waitress:
$VENV/bin/pip install "pyramid==2.0.2" waitress
