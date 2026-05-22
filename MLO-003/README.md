# MLO-001: Containerized Hugging Face FastAPI Service

## Overview
This project exposes a Hugging Face sentence-transformer model as a REST API using FastAPI, containerized with Docker.

## Project Structure
- `app/main.py`: FastAPI app
- `app/model.py`: Model loading logic
- `models/`: Model weights (cached, gitignored)
- `tests/test_api.py`: API tests

## Usage

### Build and Run (Docker)
```sh
docker build -t ml-embedder .
docker run --rm -p 8000:8000 ml-embedder
```

### Test Endpoint
```sh
curl -X POST \
  http://localhost:8000/embed \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world!"}'
```

### Environment Variables
Copy `.env.example` to `.env` and adjust as needed.

## Development
- Install requirements: `pip install -r requirements.txt`
- Run locally: `uvicorn app.main:app --reload`

## License
MIT
