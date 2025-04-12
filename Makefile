install:
	pip install -r requirements.txt

run:
	uvicorn app.main:app --reload --host=0.0.0.0 --port=8000

docker-build:
	docker build -t audiobot .

docker-run:
	docker run --env-file .env -p 8000:8000 audiobot