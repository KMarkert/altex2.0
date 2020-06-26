FROM continuumio/miniconda3:latest

USER root

RUN apt-get update && \
  apt-get install -y --no-install-recommends \
  build-essential \
  curl \
  vim \
  git && \
  apt-get autoremove -y && \
  apt-get clean && \
  rm -rf /var/lib/apt/lists/*

# install google cloud software development kit and support libraries
# Downloading gcloud package
RUN curl https://dl.google.com/dl/cloudsdk/release/google-cloud-sdk.tar.gz > /tmp/google-cloud-sdk.tar.gz

# Installing the package
RUN mkdir -p /usr/local/gcloud \
  && tar -C /usr/local/gcloud -xvf /tmp/google-cloud-sdk.tar.gz \
  && /usr/local/gcloud/google-cloud-sdk/install.sh

# Adding the package path to local
ENV PATH $PATH:/usr/local/gcloud/google-cloud-sdk/bin


RUN conda install --quiet --yes -c conda-forge \
  numpy \
  scipy \
  scikit-learn \
  fastparquet \
  pandas \
  geopandas \
  pandas-gbq \
  geojson \
  xarray \
  netCDF4 \
  flask \
  flask-cors \
  aioftp \
  aiohttp \
  fire \
  requests && \
  conda clean --all -f -y

RUN git clone https://github.com/kmarkert/altex2.0.git && \
  cd altex2.0/ && \
  git checkout backend/bigquery && \
  cd ..
