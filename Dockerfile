# Pakai Python image
FROM python:3.10

# Set direktori kerja di dalam container
WORKDIR /app

# Copy semua file ke container
COPY . /app

# Install semua dependensi
RUN pip install --no-cache-dir -r requirements.txt

# Jalankan Flask app
CMD ["python", "app.py"]
