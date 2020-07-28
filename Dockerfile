FROM ubuntu:16.04

RUN apt-get update && \ 
	apt-get -y upgrade && \
	apt-get install -y python3-pip

WORKDIR /app

COPY . /app 

RUN pip3 install -r /app/requirements.txt

EXPOSE 5000

CMD ["python3", "app.py"]