
FROM python:2

WORKDIR /opt/microservices
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py /opt/microservices/

EXPOSE 5000

WORKDIR /opt/microservices
CMD ["python", "app.py"]
