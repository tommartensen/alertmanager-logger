FROM python:3

COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt

WORKDIR /app

USER www-data

COPY main.py main.py

EXPOSE 5001

CMD [ "python3", "main.py" ]
