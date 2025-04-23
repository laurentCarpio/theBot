FROM python:3.10-slim

# Set working directory
WORKDIR /trade_app

ENV API_KEY= 'bg_8fd9f7f4f1f2b9ae5b1661eef47d472f'
ENV SECRET_KEY= '017ff9852826cf1a30c46af2fabe7d61da87ea5ff6158831eb832d8550d5e565'
ENV API_PASSPHRASE= '522723041675'

# Install basic dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    wget \
    && apt-get clean

# Copy your requirements.txt
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy your app code
COPY . .

# Set the command to run your script (replace with your actual entry point)
CMD ["python", "trade_main.py"]