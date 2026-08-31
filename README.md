# AI Code Reviewer

AI Code Reviewer is a centralized pull request review service that can operate across repositories in a GitHub organization. It integrates with Jenkins and a configurable inference API to analyze code changes and post structured review comments on pull requests.

---

## Overview

The system follows a centralized architecture:

```
┌──────────────────────┐
│    Developer PR      │
└──────────┬───────────┘
           ↓
┌──────────────────────┐
│ Orchestration Layer  │
└──────────┬───────────┘
           ↓
┌──────────────────────┐
│  AI Review Engine    │
└──────────┬───────────┘
           ↓
┌──────────────────────┐
│   GenAI Platform     │
└──────────┬───────────┘
           ↓
┌──────────────────────┐
│ Intelligent Feedback │
└──────────┬───────────┘
           ↓
┌──────────────────────┐
│  Faster Delivery     │
└──────────────────────┘
```

This eliminates the need for repository-level Jenkinsfiles and enables organization-wide automation from a single service.

---

## Features

- Organization-wide PR review without modifying individual repositories  
- Language-aware review for Node.js, Python, and Kubernetes YAML  
- Structured JSON-based comment generation  
- Inline GitHub PR comments using official APIs  
- FastAPI-based service for scalability and deployment  
- Dry-run mode for safe testing  
- Modular architecture with clear separation of concerns  

---

## Architecture

The service is structured using a layered design:

- API layer (FastAPI endpoints)  
- Service layer (business logic)  
- Client layer (GitHub and inference-provider integrations)
- Core configuration and constants  
- Models for request and response validation  

```
app/
├── api/
├── services/
├── clients/
├── models/
├── core/
├── utils/
└── main.py
```

---

## API Endpoints

### Health Check

```
GET /health
```

Response:

```json
{
  "status": "ok"
}
```

---

### Review a Pull Request

```
POST /review/pr
```

Request body:

```json
{
  "owner": "example-org",
  "repo": "example-service",
  "pull_number": 123,
  "post_comments": true
}
```

post_comments:
- true → comments will be posted to GitHub  
- false → dry run (no comments posted)  

---

## Setup

### 1. Create virtual environment

```
python3 -m venv venv
source venv/bin/activate
```

---

### 2. Install dependencies

```
pip install -r requirements.txt
```

---

### 3. Configure environment variables

```
export GITHUB_TOKEN=your_github_token
export GITHUB_API_URL=https://github.example.com/api/v3
export INFERENCE_TOKEN=your_inference_token
export INFERENCE_URL=https://inference.example.com/v1/chat/completions
export INFERENCE_MODEL=example-code-review-model
```

Or using `.env`:

```
GITHUB_TOKEN=your_github_token
GITHUB_API_URL=https://github.example.com/api/v3
INFERENCE_TOKEN=your_inference_token
INFERENCE_URL=https://inference.example.com/v1/chat/completions
INFERENCE_MODEL=example-code-review-model
```

---

### 4. Run locally

```
uvicorn app.main:app --reload
```

Service will be available at:

```
http://127.0.0.1:8000
```

---

## Testing

### Health check

```
curl http://127.0.0.1:8000/health
```

---

### Dry run PR review

```
curl -X POST http://127.0.0.1:8000/review/pr \
  -H "Content-Type: application/json" \
  -d '{
    "owner": "example-org",
    "repo": "example-service",
    "pull_number": 123,
    "post_comments": false
  }'
```

---

## Docker

### Build image

```
docker build -t ai-code-reviewer .
```

### Run container

```
docker run -p 8000:8000 \
  -e GITHUB_TOKEN=your_token \
  -e INFERENCE_TOKEN=your_token \
  ai-code-reviewer
```

---

## Jenkins Integration

Jenkins receives GitHub webhook events and invokes the service:

```
POST /review/pr
```

Jenkins extracts:
- repository name  
- pull request number  

Then calls the FastAPI service with the required payload.

---

## GitHub Integration

The service uses GitHub REST APIs to:

- Fetch PR metadata  
- Fetch changed files  
- Post inline review comments  

Required permissions:

- pull_requests: read/write  
- contents: read  

---

## Inference API Integration

The service uses a configurable chat-completions-compatible inference endpoint for code analysis. Configure the endpoint and model with `INFERENCE_URL` and `INFERENCE_MODEL`.

Each file is processed with a language-specific prompt and the response is parsed into structured comments.

---

## Development Notes

- Use post_comments=false during testing  
- Logs are available via standard output  
- Invalid model responses are handled gracefully  
- Unsupported file types are skipped  

---

## Future Enhancements

- Direct GitHub webhook endpoint in FastAPI  
- Async processing using a queue or event stream
- Retry and dead-letter queue handling  
- Observability and metrics  
- Prompt versioning and experimentation  

---

## License

Add a license appropriate for your organization before distributing this project.
