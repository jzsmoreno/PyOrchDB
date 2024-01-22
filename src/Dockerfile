# Use a Python 3.10.13 slim image based on Debian bookworm as the base image
FROM python:3.10.13-slim-bookworm

# Set the working directory in the Docker container
WORKDIR /home/app/

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

# Copy requirements.txt to the docker image and install Python packages
COPY ./requirements.txt .
RUN pip3 install --upgrade pip && \
    pip3 install -r requirements.txt && \
    rm requirements.txt

# Extra to debug but not necessary
RUN pip3 install --no-cache-dir jupyterlab
EXPOSE 8888

# Expose port 8888 for Jupyter Notebook
EXPOSE 8501

# Instructions for running the Docker container:
# docker run -p 8501:8501 -v /path/to/this/repo:/home/app/ <image_name> <command>

