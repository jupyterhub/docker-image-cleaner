FROM ubuntu:22.04

# FAIL: build fails (leaves dangling image layers)
ARG FAIL=0
# SIZE_KB: size of intermediate layer in kB (created with dd)
ARG SIZE_MB=1000

USER root
RUN dd if=/dev/urandom bs=1M count=$SIZE_MB of=newfile

RUN exit $FAIL
