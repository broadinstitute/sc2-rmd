FROM r-base:4.0.4

WORKDIR /

COPY requirements-R.txt /docker/

RUN R -e "install.packages(read.table('/docker/requirements-R.txt')$V1, repos='https://cloud.r-project.org')"

COPY . /docker/

