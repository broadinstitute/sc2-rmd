FROM r-base:4.0.4

WORKDIR /

COPY requirements-R.txt /docker

RUN for pkg in `cat /docker/requirements-R.txt`; do R -e "install.packages(c('$pkg'))"; done

COPY . /docker

