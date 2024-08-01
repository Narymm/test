install:
		pip install poetry && \
		poetry install

start:
		poetry run python -m flask run --host=0.0.0.0 --port=10000 & \
		poetry run python test/trying.py
	