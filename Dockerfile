FROM python:3

ENV latitude='0'
ENV longitude='0'
ENV distance='0'
ENV useMQTT='FALSE'
ENV mqttBroker=''
ENV mqttUser='0'
ENV mqttPass='0'
ENV mqttBase='0'

WORKDIR /usr/src/app

COPY requirements.txt ./

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "./runme.py"]