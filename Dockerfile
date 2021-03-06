FROM ubuntu:focal-20210217

LABEL maintainer "Daniel Park <dpark@broadinstitute.org>"

# non-interactive session just for build
ARG DEBIAN_FRONTEND=noninteractive

# update apt database and install R apt repo
RUN apt-get update && \
  apt-get -y -qq install software-properties-common && \
  apt-key adv --keyserver keyserver.ubuntu.com --recv-keys E298A3A825C0D65DFD57CBB651716619E084DAB9 && \
  add-apt-repository 'deb https://cloud.r-project.org/bin/linux/ubuntu focal-cran40/' && \
  apt-get update

# install all desired packages
RUN apt-get -y -qq install \
    less nano vim git wget curl jq zstd parallel locales \
    gnupg libssl-dev libcurl4-openssl-dev \
    pandoc pandoc-citeproc \
    libxml2 libxml2-dev \
    imagemagick libmagick++-dev \
    texlive-base texlive-latex-recommended texlive texlive-latex-extra texlive-extra-utils texlive-fonts-extra \
    fonts-roboto \
    python3 python3-pip python3-pandas python3-plotly \
    r-base r-base-dev \
  && apt-get clean

# Set default locale to en_US.UTF-8
RUN locale-gen en_US.UTF-8
ENV LANG="en_US.UTF-8" LANGUAGE="en_US:en" LC_ALL="en_US.UTF-8"

# Install R packages
RUN R -e "install.packages(c( \
  'devtools', 'tidyverse', 'sf', \
  'knitr', 'rmarkdown', 'tinytex', 'reticulate', 'kableExtra', \
  'ggplot2', 'ggthemes', 'dplyr', 'plyr', \
  'plotly', \
  'RColorBrewer', 'viridis', 'viridisLite', \
  'phytools' ))"

# Install Python
RUN pip3 install epiweeks

# Bring in other supporting files
COPY . /docker/

WORKDIR /

CMD ["/bin/bash"]
