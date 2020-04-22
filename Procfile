web: python src/serve.py
beat: sh start.sh;celery -A core beat --workdir src -l info
urgent: sh start.sh;celery -A core worker -Q urgent --workdir src -l info
general: sh start.sh;celery -A core worker -Q general --workdir src -l info