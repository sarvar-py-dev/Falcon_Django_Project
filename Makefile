mig:
	python3 manage.py makemigrations
	python3 manage.py migrate

beat:
	celery -A root beat -l INFO --scheduler django_celery_beat.schedulers:DatabaseScheduler

celery:
	celery -A root worker -l INFO

flower:
	celery -A root.celery.app flower --port=5001

dumpdata:
	python3 manage.py dumpdata --indent=2 apps.Category > categories.json

loaddata:
	python3 manage.py loaddata categories
