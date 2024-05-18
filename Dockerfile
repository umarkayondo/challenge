# Use the official Python image from the Docker Hub, specifying the version to ensure consistency
FROM python:3.10.6-buster

# Upgrade pip to the latest version
RUN pip install --upgrade pip

# Prevent Python from writing .pyc files to disk
ENV PYTHONDONTWRITEBYTECODE=1

# Disable Python output buffering to make logging easier
ENV PYTHONUNBUFFERED=1

# Expose the container's port to the host machine, defaulting to 8000 if $EXPOSED_CONTAINER_PORT is not set
EXPOSE ${EXPOSED_CONTAINER_PORT:-8000}

# Set the working directory inside the container to /app
WORKDIR /app

# Update the package lists to ensure we get the latest versions
RUN apt-get update && apt-get install -y curl

# Install ODBC library, which may be needed for database connectivity
RUN apt-get install -y libodbc1

# Install Unix ODBC, which provides the ODBC system for database access
RUN apt install -y unixodbc

# Install necessary packages for compiling and installing Python dependencies
RUN apt-get install -y gcc libc-dev python3-dev musl-dev unixodbc-dev

# Copy the requirements.txt file into the container
COPY requirements.txt requirements.txt

# Install the Python dependencies specified in the requirements.txt file without using the cache
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --force-reinstall 'sqlalchemy<2.0.0'

# Copy the entire contents of the current directory into the container's /app directory
COPY . .

# Specify the command to run the application using uvicorn, with the host and port configured
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port $EXPOSED_CONTAINER_PORT"]