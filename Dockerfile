FROM python:2.7.12
MAINTAINER "Henrik Nårstad"

RUN useradd -m narhen
USER narhen

WORKDIR /home/narhen/app
COPY requirements.txt .
COPY components ./components

USER root
RUN pip install -r requirements.txt

USER narhen
ENTRYPOINT ["python", "components/controller.py"]
