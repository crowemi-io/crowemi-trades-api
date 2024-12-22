FROM python:3.12

RUN apt-get update && apt-get install

WORKDIR /app

COPY requirements.txt requirements.txt

COPY common/helper.py common/helper.py

COPY data/client.py data/client.py

COPY models/base.py models/base.py
COPY models/order.py models/order.py
COPY models/watchlist.py models/watchlist.py

COPY trading/trading_client.py trading/trading_client.py
COPY trading/alpaca_client.py trading/alpaca_client.py
COPY trading/coinbase_client.py trading/coinbase_client.py

COPY trader.py trader.py

COPY routers/ routers/
COPY api.py api.py

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

EXPOSE 8080

# ENTRYPOINT [ "sh" ]
CMD ["fastapi", "run", "api.py", "--port", "8080"]
