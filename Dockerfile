FROM python:3.11.7

COPY ./ /data
WORKDIR /data

RUN apt-get update && apt-get install -y ffmpeg
RUN pip install -r requirements.txt

CMD [ "python3", "-m", "src.main" ]
