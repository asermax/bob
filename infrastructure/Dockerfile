# syntax=docker/dockerfile:1

# =============================================================================
# Bob's Autonomous Harness - Docker Image
# =============================================================================
# Alpine-based image with Python, Node.js, and Claude Code CLI.
# The harness and dashboard code are mounted from the host, not copied.
# Runs as non-root user to allow --dangerously-skip-permissions.
# =============================================================================

FROM alpine:3.21

WORKDIR /bob

# Install Python, Node.js, pip, git, ssh, and runtime dependencies
RUN apk add --no-cache \
    python3 \
    py3-pip \
    nodejs \
    npm \
    bash \
    git \
    openssh-client \
    libffi \
    su-exec

# Install Claude Code CLI globally
RUN npm install -g @anthropic-ai/claude-code \
    && npm cache clean --force

# Install Python packages globally (no venv)
RUN pip3 install --break-system-packages \
    claude-code-sdk \
    fastapi \
    "uvicorn[standard]" \
    jinja2

# Create non-root user for running Claude CLI with bypass permissions
RUN addgroup -g 1000 bob && \
    adduser -u 1000 -G bob -h /home/bob -s /bin/bash -D bob

# Bob's workspace will be mounted at /bob (includes infrastructure/)
ENV BOB_WORKSPACE=/bob

# Dashboard port
EXPOSE 3141

# Entrypoint comes from the mounted workspace - no need to copy
ENTRYPOINT ["/bob/infrastructure/entrypoint.sh"]
CMD ["both"]
