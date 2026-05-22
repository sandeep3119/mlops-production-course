FROM python:3.10-slim

WORKDIR /mlo-001

RUN pip install torch --index-url https://download.pytorch.org/whl/cpu

# Install dependencies
COPY app/ ./
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Download model at build time
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2', cache_folder='/mlo-001/app/models')"

# Expose port
EXPOSE 8000


# Start FastAPI app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
