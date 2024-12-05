# Use the official Python image as a base image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install required dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Command to run the bot
CMD ["python", "bot.py"]
