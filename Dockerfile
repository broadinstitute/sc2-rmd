FROM ubuntu:focal-20210217

LABEL maintainer "Daniel Park <dpark@broadinstitute.org>"

# Set default locale to en_US.UTF-8
ENV LANG="en_US.UTF-8" LANGUAGE="en_US:en" LC_ALL="en_US.UTF-8" DEBIAN_FRONTEND=noninteractive

# non-interactive session
RUN echo 'debconf debconf/frontend select Noninteractive' | debconf-set-selections

RUN apt-get update && \
  apt-get -y -qq install \
    less git wget curl jq zstd parallel \
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

COPY . /docker/

WORKDIR /

CMD ["/bin/bash"]
