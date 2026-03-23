# Don't Remove Credit @vlcbox
# Subscribe YouTube Channel For Amazing Bot @vlcbox
# Ask Doubt on telegram @rickakhtar

FROM python:3.10.8-slim-buster

RUN apt update && apt upgrade -y
RUN apt install git ffmpeg -y
COPY requirements.txt /requirements.txt

RUN cd /
RUN pip3 install -U pip && pip3 install -U -r requirements.txt
RUN mkdir /VLCBOX-Filter-Bot
WORKDIR /VLCBOX-Filter-Bot
COPY . /VLCBOX-Filter-Bot
CMD ["python", "bot.py"]

