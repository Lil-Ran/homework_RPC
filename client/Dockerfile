FROM python:alpine

RUN adduser -D -h /home/rpc rpc && \
    mkdir -p /home/rpc/client/ && \
    chown -R rpc:rpc /home/rpc

COPY --chown=rpc:rpc --chmod=755 client_core.py client_test.py config.json /home/rpc/client/

WORKDIR /home/rpc/client
USER rpc

CMD ["python", "client_test.py"]
