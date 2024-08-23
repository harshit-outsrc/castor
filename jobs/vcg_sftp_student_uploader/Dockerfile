FROM python:3.11-slim
RUN apt update && apt install -y git
RUN mkdir ~/.ssh && touch ~/.ssh/config && echo "Host github.com\n\tStrictHostKeyChecking no\n" >> ~/.ssh/config
WORKDIR /vcg_sftp_student_uploader
ADD requirements.txt .
RUN --mount=type=ssh pip install -r requirements.txt\
    --no-cache
ADD . .

ENTRYPOINT ["python3"]
CMD ["vcg_script.py", "-m"]