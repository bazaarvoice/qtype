FROM python:3.12-slim

WORKDIR /app

# Install uv for fast dependency management
RUN pip install --no-cache-dir uv

# Copy project definition first and install dependencies (cached layer)
COPY pyproject.toml .
RUN uv pip install --system .

# Copy the Python module source (changes more often than dependencies)
COPY {{ cookiecutter.__module }}/ ./{{ cookiecutter.__module }}/

# Copy QType application files
COPY *.qtype.yaml .

# Expose the default QType server port
EXPOSE 8000

# Start the QType server
CMD ["qtype", "serve", "{{ cookiecutter.__slug }}.qtype.yaml"]
