FROM python:3.11-slim
RUN apt update && apt install -y git
RUN mkdir /root/.ssh && touch /root/.ssh/config && echo "Host github.com\n\tStrictHostKeyChecking no\n" >> /root/.ssh/config
WORKDIR src
ADD requirements.txt .
RUN --mount=type=ssh pip install -r requirements.txt
ADD . .

ENTRYPOINT ["python", "main.py"]