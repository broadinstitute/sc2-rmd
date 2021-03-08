FROM quay.io/broadinstitute/viral-rmd:latest

LABEL maintainer "Daniel Park <dpark@broadinstitute.org>"

# Bring in other supporting files
COPY . /docker/

WORKDIR /

CMD ["/bin/bash"]
