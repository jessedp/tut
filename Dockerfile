# syntax=docker/dockerfile:1

# Comments are provided throughout this file to help you get started.
# If you need more help, visit the Dockerfile reference guide at
# https://docs.docker.com/engine/reference/builder/

ARG PYTHON_VERSION=3.11.6
FROM python:${PYTHON_VERSION}-slim as base

# Prevents Python from writing pyc files.
ENV PYTHONDONTWRITEBYTECODE=1

# Keeps Python from buffering stdout and stderr to avoid situations where
# the application crashes without emitting any logs due to buffering.
ENV PYTHONUNBUFFERED=1

# Install ffmpeg libraries needed to transcode Tablo video files.
RUN apt-get update && apt-get install -y ffmpeg

WORKDIR /app

# Create a non-privileged user that the app will run under.
# See https://docs.docker.com/develop/develop-images/dockerfile_best-practices/#user
# Default Synology DSM first uid. See comments below for more context.
ARG UID=1026
RUN adduser \
    --disabled-password \
    --gecos "" \
    --shell "/sbin/nologin" \
    --uid "${UID}" \
    appuser

# GID hacks for Synology DSM. Try as best we can to replicate DSM's default
# primary ("100(users)") and secondary group membership ("101(administrators)")
# to overcome permission issues with writing to a bind mounted folder, while
# still being somewhat platform agnostic. Example of the issue:
# https://www.reddit.com/r/synology/comments/s1arg0/synology_and_docker_permission_problem/
# TODO: Make gid's user configurable.
RUN usermod -g users appuser
RUN adduser appuser `cat /etc/group | grep ":101:" | cut -d':' -f1`

# Download dependencies as a separate step to take advantage of Docker's caching.
# Leverage a cache mount to /root/.cache/pip to speed up subsequent builds.
# Leverage a bind mount to requirements.txt to avoid having to copy them into
# into this layer.
RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=bind,source=requirements.txt,target=requirements.txt \
    python -m pip install -r requirements.txt

# Switch to the non-privileged user to run the application.
USER appuser

# Copy the source code into the container.
COPY . .

# Build the shows db.
# TODO: Run this separately for now.
# RUN python3 tut.py config --discover

# Check if ~/Tablo directory is mounted. Ideally this is run before each tut.py
# command (or tut.py is modified to not implicitly create a ~/Tablo directory)
# so that we don't accidentally sync shows into the container.
# TODO: Also check we have the right read/write permissions.
# Then sync all shows.
CMD if [ ! -d "/home/appuser/Tablo" ]; then echo "/home/appuser/Tablo not mounted." && exit 1; fi; \
  python3 tut.py library --build && \
  python3 tut.py -L search | \
  python3 tut.py copy
