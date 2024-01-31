FROM python:3.11.7-alpine

COPY ./ /data
WORKDIR /data

RUN pip install -r requirements.txt

CMD [ "./run.sh" ]