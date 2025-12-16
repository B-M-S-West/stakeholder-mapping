FROM python:3.11-slim

# Install uv.
COPY --from=ghcr.io/astral-sh/uv:0.9.8 /uv /uvx /bin/

# Set the working directory
WORKDIR /app

# Install Dependencies First
COPY pyproject.toml uv.lock* ./

# Install dependencies
RUN uv sync --frozen --no-cache

# Copy the application code
COPY . .

EXPOSE 8501

CMD ["uv", "run", "streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]

# Build the docker image
# docker buildx build -t stakeholder-mapping --load .