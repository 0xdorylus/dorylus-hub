curl -sSL https://install.python-poetry.org | python3 -
poetry env use python3.10
poetry shell
poetry install


flower==1.2.0
 poetry add flower==1.2.0

## Sending a Task to Celery

(venv)$ celery -A main.celery worker --loglevel=info


>>> from main import app, divide
>>> task = divide.delay(1, 2)
>

>>> print(task.state, task.result)
PENDING None

>>> print(task.state, task.result)
SUCCESS 0.5



## Monitoring Celery with Flower

celery -A main.celery flower --port=5555
