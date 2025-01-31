#!/usr/bin/env bash

set -ex

# Install python
apt-get install -y python3 python3.10 python3-pip python3-dev jq
# Upgrade pip
python3.10 -m pip install -U --force-reinstall pip
# Install gspack dependencies
python3.10 -m pip install subprocess32 numpy scipy matplotlib
# Install solution script dependencies
if [[ -f "/autograder/source/requirements.txt" ]]; then
    python3.10 -m pip install -r /autograder/source/requirements.txt
fi

git clone https://github.com/jakobkotas/gspack
cd gspack || exit
python3.10 setup.py install
cd .. || exit

matlab=$(jq '.matlab_support' /autograder/source/config.json)
if [ $matlab = 1 ]; then
  echo "Adding MATLAB components"
  # Set up MATLAB, if needed
  chmod +x /autograder/source/matlab_setup.sh
  /autograder/source/matlab_setup.sh
fi

jupyter=$(jq '.jupyter_support' /autograder/source/config.json)
if [ $jupyter = 1 ]; then
    echo "Adding Jupyter components"
    python3.10 -m pip install ipython nbformat
fi

echo "Main setup.sh completed"
