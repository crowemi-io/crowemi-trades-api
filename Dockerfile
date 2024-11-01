FROM python:3.12

RUN apt-get update && apt-get install

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

ENTRYPOINT [ "sh" ]
