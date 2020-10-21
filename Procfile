web: python src/serve.py
beat: celery -A core beat --workdir src -l info
urgent: celery -A core worker -Q urgent --workdir src -l info
general: celery -A core worker -Q general --workdir src -l info