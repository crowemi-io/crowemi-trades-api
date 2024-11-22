FROM python:3.12

RUN apt-get update && apt-get install

WORKDIR /app

COPY requirements.txt requirements.txt
COPY common/alpaca.py common/alpaca.py
COPY common/helper.py common/helper.py
COPY data/client.py data/client.py
COPY data/models.py data/models.py
COPY trader.py trader.py

COPY routers/ routers/
COPY api.py api.py

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

EXPOSE 8080

# ENTRYPOINT [ "sh" ]
CMD ["fastapi", "run", "api.py", "--port", "8080"]
