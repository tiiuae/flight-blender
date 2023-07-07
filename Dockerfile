FROM python:3.9
ENV PYTHONUNBUFFERED=1
RUN apt-get update &&\
    apt-get install -y libgdal-dev


RUN mkdir /app
WORKDIR /app
COPY requirements.txt /app/
RUN pip install -r requirements.txt


ARG CPLUS_INCLUDE_PATH=/usr/include/gdal
ARG C_INCLUDE_PATH=/usr/include/gdal
RUN pip install gdal==3.6.2

RUN rm -rf __pycache__
COPY . /app/