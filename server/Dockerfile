FROM python:alpine

RUN adduser -D -h /home/rpc rpc && \
    mkdir -p /home/rpc/server/services/ && \
    chown -R rpc:rpc /home/rpc

COPY --chown=rpc:rpc --chmod=755 server_main.py config.json /home/rpc/server/
COPY --chown=rpc:rpc --chmod=755 services/** /home/rpc/server/services/

WORKDIR /home/rpc/server
USER rpc

CMD ["python", "server_main.py"]
