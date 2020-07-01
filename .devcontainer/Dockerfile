FROM mcr.microsoft.com/vscode/devcontainers/python:0-3.7

WORKDIR /workspaces

# Install Python dependencies from requirements.txt if it exists
COPY requirements.txt requirements_tests.txt ./
RUN pip3 install -r requirements.txt -r requirements_tests.txt \
    && pip3 install tox \
    && rm -f requirements.txt requirements_tests.txt
