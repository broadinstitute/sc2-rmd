FROM ubuntu:focal-20210217

WORKDIR /

RUN apt-get update && \
  apt-get -y install \
    less git wget curl jq zstd \
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

