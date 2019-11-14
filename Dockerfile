FROM arm32v7/python:3.7-slim-buster
RUN apt update && apt install -y gcc 
RUN apt install -y zlib1g-dev \
  libjpeg62-turbo-dev \
  libfreetype6-dev \
  fonts-dejavu-core
WORKDIR /app/
COPY requirements.txt /app/
RUN pip3 install -r requirements.txt
RUN apt remove -y gcc \
  && apt autoremove -y \
  && apt clean
COPY *.py /app/
ENTRYPOINT python3 ruuvitag_epaper.py 
