FROM ubuntu:14.04


RUN apt-get -qq update && apt-get install -y \
    git-core \
    curl \
    libpython-dev \
    libev4 \
    libev-dev \
    libffi6 \
    libffi-dev \
    libssl-dev \
    python-dev \
    && rm -rf /var/lib/apt/lists/*

RUN curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py && python get-pip.py pip==9.0.3

COPY ./docker/dev/dev-requirements.txt /etc/requirements.txt
RUN sudo pip install -r /etc/requirements.txt

COPY ./docker/dev/run-worker.sh /usr/local/bin/run-worker
COPY ./docker/dev/run-server.sh /usr/local/bin/run-server
COPY ./docker/dev/startup.sh /usr/local/bin/poppy_startup
RUN chmod 755 /usr/local/bin/poppy_startup \
 /usr/local/bin/run-worker \
 /usr/local/bin/run-server

# Set up the configuration files
COPY ./docker/dev/poppy.conf /etc/poppy.conf
COPY ./docker/dev/logging.conf /etc/logging.conf

ADD . /poppy

RUN sudo pip install -e /poppy

COPY ./docker/dev/_init_setup.sh /usr/local/bin/init-poppy-setup
RUN chmod +x /usr/local/bin/init-poppy-setup

# Uncomment to run without compose
# EXPOSE 8888
# CMD poppy_startup

