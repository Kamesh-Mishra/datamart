FROM python:3.6

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app
RUN pip install aio-pika elasticsearch
RUN pip install requests sodapy
COPY datamart_core datamart_core
RUN pip install -e /usr/src/app/datamart_core
COPY discovery/socrata /usr/src/app/socrata
RUN pip install -e socrata
CMD ["python", "socrata/datamart_socrata_discovery.py"]