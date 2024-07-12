FROM python:alpine

RUN adduser -D -h /home/rpc rpc && \
    mkdir -p /home/rpc/register-center/ && \
    chown -R rpc:rpc /home/rpc

COPY --chown=rpc:rpc --chmod=755 reg_center_main.py config.json /home/rpc/register-center/

WORKDIR /home/rpc/register-center
USER rpc

CMD ["python", "reg_center_main.py"]
