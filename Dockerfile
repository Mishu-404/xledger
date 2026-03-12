[Region: us-west1]
=========================
Using Detected Dockerfile
=========================
context: 6nhj-KwOL
internal
load build definition from Dockerfile
0ms
internal
load metadata for docker.io/library/python:3.11-slim
409ms
auth
library/python:pull token for registry-1.docker.io
0ms
internal
load .dockerignore
0ms
1
FROM docker.io/library/python:3.11-slim@sha256:d6e4d224f70f9e0172a06a3a2eba2f768eb146811a349278b38fff3a36463b47 cached
16ms
internal
load build context
0ms
2
RUN apt-get update && apt-get install -y     libpango-1.0-0     libpangoft2-1.0-0     libpangocairo-1.0-0     libcairo2     libgdk-pixbuf2.0-0     libffi-dev     shared-mime-info     fonts-noto-core     fonts-noto-extra     && fc-cache -fv     && rm -rf /var/lib/apt/lists/*
4s
Hit:1 http://deb.debian.org/debian trixie InRelease
Get:2 http://deb.debian.org/debian trixie-updates InRelease [47.3 kB]
Get:3 http://deb.debian.org/debian-security trixie-security InRelease [43.4 kB]
Get:4 http://deb.debian.org/debian trixie/main amd64 Packages [9670 kB]
Get:5 http://deb.debian.org/debian trixie-updates/main amd64 Packages [5412 B]
Get:6 http://deb.debian.org/debian-security trixie-security/main amd64 Packages [108 kB]
Fetched 9875 kB in 2s (5632 kB/s)
Reading package lists...
Reading package lists...
Building dependency tree...
Reading state information...
Package libgdk-pixbuf2.0-0 is not available, but is referred to by another package.
This may mean that the package is missing, has been obsoleted, or
is only available from another source
However the following packages replace it:
  libgdk-pixbuf-xlib-2.0-0
E: Package 'libgdk-pixbuf2.0-0' has no installation candidate
Dockerfile:4
-------------------
3 |     # Install system dependencies for WeasyPrint + Bengali font
4 | >>> RUN apt-get update && apt-get install -y \
5 | >>>     libpango-1.0-0 \
6 | >>>     libpangoft2-1.0-0 \
7 | >>>     libpangocairo-1.0-0 \
8 | >>>     libcairo2 \
9 | >>>     libgdk-pixbuf2.0-0 \
10 | >>>     libffi-dev \
11 | >>>     shared-mime-info \
12 | >>>     fonts-noto-core \
13 | >>>     fonts-noto-extra \
14 | >>>     && fc-cache -fv \
15 | >>>     && rm -rf /var/lib/apt/lists/*
16 |
-------------------
ERROR: failed to build: failed to solve: process "/bin/sh -c apt-get update && apt-get install -y     libpango-1.0-0     libpangoft2-1.0-0     libpangocairo-1.0-0     libcairo2     libgdk-pixbuf2.0-0     libffi-dev     shared-mime-info     fonts-noto-core     fonts-noto-extra     && fc-cache -fv     && rm -rf /var/lib/apt/lists/*" did not complete successfully: exit code: 100
You reached the end of the range
Mar 11, 2026, 7:43 PM
