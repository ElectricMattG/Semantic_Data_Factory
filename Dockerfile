# Use a Python 3 base image
FROM python:3.9

# Set the working directory to /research
WORKDIR /TAL_DML_Semantic_Data_Factory

# Copy the requirements file into the container
COPY requirements.txt .

# Install any dependencies specified in the requirements file
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire research directory into the container
COPY . .

# Set the entrypoint to run the main.py file inside the src directory
ENTRYPOINT ["python", "-m", "src.main"]