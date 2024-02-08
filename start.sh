set -eux
. /tmp/venv/bin/activate
flask --app app run --port $PORT --debug
