# Use a Python 3.10.13 slim image based on Debian bookworm as the base image
FROM python:3.10.13-slim-bookworm

# Set the working directory in the Docker container
WORKDIR /home/app/

# Update the package list and install required dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        jq \
        && rm -rf /var/lib/apt/lists/*

RUN curl -sL https://aka.ms/InstallAzureCLIDeb | bash

# Install necessary tools and add Microsoft's public key for package verification
RUN apt-get update && apt-get install -y \
    curl \
    apt-transport-https \
    gnupg \
    git

# Add Microsoft's public key for SQL Server ODBC drivers
RUN curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > microsoft.gpg
RUN install -o root -g root -m 644 microsoft.gpg /usr/share/keyrings/
RUN echo "deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft.gpg] https://packages.microsoft.com/debian/12/prod bookworm main" > /etc/apt/sources.list.d/mssql-release.list

# Update package list and install Microsoft ODBC SQL Server driver
RUN apt-get update && ACCEPT_EULA=Y apt-get install -y msodbcsql17

# Install additional dependencies
RUN apt-get install -y g++ unixodbc-dev unixodbc

ENV SHELL=/bin/bash

# Copy requirements.txt to the docker image and install Python packages
COPY ./requirements.txt .
RUN pip3 install --upgrade pip && \
    pip3 install -r requirements.txt && \
    rm requirements.txt

# Extra to debug but not necessary
RUN pip3 install --no-cache-dir jupyterlab
RUN pip3 install --no-cache-dir streamlit
EXPOSE 8888

# Expose port 8888 for Jupyter Notebook
EXPOSE 8501

# Set a default command (modify as needed)
# CMD ["bash"]
