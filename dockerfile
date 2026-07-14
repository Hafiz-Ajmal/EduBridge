FROM python:3.14.5

WORKDIR  /app 

COPY ./requirements.txt requirements.txt

RUN pip install --no-cache-dir -r requirements.txt
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

RUN useradd -m ajmal



COPY . /app

RUN chown -R ajmal:ajmal /app

User ajmal

CMD ["uvicorn","main:a Superuser (admin only)pp","--host","0.0.0.0","--port","8000"]

