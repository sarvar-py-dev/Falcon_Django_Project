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

loaddata:z
	python3 manage.py loaddata categories

make_image:
	docker build -t falcon_tmp_image .

container:
	docker run --name falcon_tmp_container -p 8000:8088 -d falcon_tmp_image