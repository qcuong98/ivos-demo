if [[ $1 ]]; then
  gunicorn server.api:app --bind 0.0.0.0:$1 --timeout 30 --threads 4
else
  gunicorn server.api:app --bind 0.0.0.0:8000 --timeout 30 --threads 4
fi