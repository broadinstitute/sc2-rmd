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
    texlive-base texlive-latex-recommended texlive texlive-latex-extra \
    fonts-roboto \
    python3 python3-pandas python3-plotly \
    r-base r-base-dev \
    r-cran-devtools \
    r-cran-tidyverse \
    r-cran-sf \
    r-cran-reticulate \
    r-cran-rmarkdown r-cran-knitr r-cran-tinytex \
    r-cran-ggplot2 r-cran-ggthemes \
    r-cran-dplyr r-cran-plyr \
    r-cran-plotly \
    r-cran-rcolorbrewer r-cran-viridis r-cran-viridislite \
    r-cran-phytools \
  && apt-get clean

# Set default locale to en_US.UTF-8
RUN locale-gen en_US.UTF-8
ENV LANG="en_US.UTF-8" LANGUAGE="en_US:en" LC_ALL="en_US.UTF-8"


COPY . /docker/

WORKDIR /

CMD ["/bin/bash"]
