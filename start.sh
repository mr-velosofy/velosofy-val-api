set -eux
. /tmp/venv/bin/activate
flask --app main run --port $PORT
