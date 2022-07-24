# syntax=docker/dockerfile:1
FROM python:3

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /src
ADD requirements/pro-ext.txt requirements.txt
ADD hydrus_dd-3.0.0-py3-none-any.whl /src/
RUN pip install hydrus_dd-3.0.0-py3-none-any.whl --proxy http://faviannys:huracan840125*@10.12.34.153:80
RUN pip install -r requirements.txt --proxy http://faviannys:huracan840125*@10.12.34.153:80
ADD ./model ~/model
ADD ./src/ /src/
