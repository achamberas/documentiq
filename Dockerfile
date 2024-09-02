# app/Dockerfile

FROM python:3.9-slim

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . ./

RUN pip install --upgrade pip
RUN pip3 install -r requirements.txt

EXPOSE 8080

ENV PYTHONUNBUFFERED True
ENV LISTEN_PORT 8080
ENV PORT 8080

# HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

#CMD exec gunicorn --bind :$PORT --workers 2 --threads 8 --timeout 0 main:app
ENTRYPOINT ["streamlit", "run", "Documents.py", "--server.port= 8080", "--server.address=0.0.0.0"]
