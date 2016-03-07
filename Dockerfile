FROM thefactory/python
MAINTAINER Vivek vivek@gsshop.com

ADD . /opt/marathon-logger
RUN pip install -r /opt/marathon-logger/requirements.txt

EXPOSE 5000
ENTRYPOINT ["/opt/marathon-logger/marathon-logger.py", "-p", "5000"]
CMD "-h"
