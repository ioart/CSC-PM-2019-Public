FROM python:3

RUN pip install redis flask pymongo

COPY echo-server.py /

COPY logging.conf /

EXPOSE 5000

ENTRYPOINT ["python", "echo-server.py"]
