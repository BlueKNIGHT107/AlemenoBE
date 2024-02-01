# We Use an official Python runtime as a parent image
FROM python:3.8

# Declaring enviroment variables to ensure that the python output is set straight
# to console and pyc files are not written to disk
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

# Set the working directory to
WORKDIR /CreditApprovalSystem

# Copy the current directory contents into the container
COPY . .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
