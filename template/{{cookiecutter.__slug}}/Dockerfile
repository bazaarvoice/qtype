FROM python:3.12-slim

WORKDIR /app

# Install uv for fast dependency management
RUN pip install --no-cache-dir uv

# Copy project definition and Python module first (for layer caching)
COPY pyproject.toml .
COPY {{ cookiecutter.__module }}/ ./{{ cookiecutter.__module }}/

# Install the project and all dependencies
RUN uv pip install --system .

# Copy QType application files
COPY *.qtype.yaml .

# Expose the default QType server port
EXPOSE 8000

# Start the QType server
CMD ["qtype", "serve", "{{ cookiecutter.__slug }}.qtype.yaml"]
