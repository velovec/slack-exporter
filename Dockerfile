FROM python:2.7

MAINTAINER Alexey Deryugin <velovec@gmail.com>

COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt && rm /tmp/requirements.txt

COPY slack.py /slack/slack.py

WORKDIR /slack

ENTRYPOINT ["python", "slack.py"]