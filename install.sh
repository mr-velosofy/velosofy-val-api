set -eux
# Two things:
# 1. Python doesn't come with pip. Setting up a venv installs pip.
# 2. This keeps us from installing dependencies into /app, which saves project
#    disk space.
python3 -m venv /tmp/venv
. /tmp/venv/bin/activate
python3 -m pip --cache-dir /tmp/pip-cache install -r requirements-stealth.txt
pip install --upgrade pip