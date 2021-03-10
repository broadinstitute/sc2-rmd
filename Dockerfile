FROM quay.io/broadinstitute/viral-rmd:0.1.3

LABEL maintainer "Daniel Park <dpark@broadinstitute.org>"

# Bring in other supporting files
COPY . /docker/

WORKDIR /

CMD ["/bin/bash"]
