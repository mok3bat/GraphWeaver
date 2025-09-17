# ----------------------------
# Stage 1: Builder
# ----------------------------
    FROM python:3.12-slim AS builder

    WORKDIR /app
    
    # Install build dependencies
    RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential gcc curl && \
        rm -rf /var/lib/apt/lists/*
    
    # Copy requirements and install deps into a temp directory
    COPY requirements.txt .
    RUN pip install --no-cache-dir --prefix=/install -r requirements.txt
    
    
    # ----------------------------
    # Stage 2: Runtime
    # ----------------------------
    FROM python:3.12-slim AS runtime
    
    WORKDIR /app
    
    # Copy installed packages from builder
    COPY --from=builder /install /usr/local
    
    # Copy app source
    COPY . .
    
    # Default envs (can be overridden)
    ENV HOST=0.0.0.0 \
        PORT=7860 \
        LLM_MODEL=gpt-4o-mini
    
    EXPOSE 7860
    
    CMD ["python", "app.py"]
    