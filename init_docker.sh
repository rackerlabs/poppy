#!/usr/bin/env bash

## This file shouldn't need to be modified unless you want to override something.
## Use the '.env' file located in the root of the poppy repo to configure.

WORKSPACE=$(cd $(dirname "${BASH_SOURCE[0]}") && pwd);
REBUILD=1
AUTORUN=1

# copy the requirements so they can be cached within docker
{
    find "$WORKSPACE/requirements" -name "*.txt" -exec cat "{}" \; | grep -v "^-r"
    cat "$WORKSPACE/doc/requirements.txt"
    cat "$WORKSPACE/tests/test-requirements.txt"
}  | sort | uniq | tee "$WORKSPACE/docker/dev/dev-requirements.txt"


 find "$WORKSPACE/requirements" -name "*.txt" -exec cat "{}" \; | sort
# Check for a "dev" poppy config first, fall back to generating a new one from .env
if [ -f "$HOME/.poppy/poppy-dev.conf" ]; then
    cp "$HOME/.poppy/poppy-dev.conf" "$WORKSPACE/docker/dev/poppy.conf"
else
    if [ ! -f "$WORKSPACE/docker/dev/poppy.conf" ] || [ "$REBUILD" ]; then
        echo "Running initial setup"

        set -a
        . "$WORKSPACE/.env"
        set +a

        if [ "$(uname -s)" = "Darwin" ]; then
            # Using docker for mac
            unset DOCKER_HOST

            if [ ! -x "/usr/local/bin/gettext" ]; then
                    brew install gettext
                    brew link gettext --force
            fi
            if [ ! -x "/usr/local/bin/ip" ]; then
                brew install gettext iproute2mac
            fi
        fi
        export HOST_IP=$(ip route get 1 | awk '{print $NF;exit}')
        cd "$WORKSPACE/docker/dev"
        # Generate a new poppy.conf from the .env file
        cat poppy.conf.template | envsubst > poppy.conf
    fi
fi

cd "$WORKSPACE"

if [ "$AUTORUN" ]; then
    docker-compose up --build -d
    docker ps
    sleep 5
    exec "$WORKSPACE/docker/dev/_init_setup.sh"
    # docker-compose  exec  poppy-server  "init-poppy-setup"
fi
