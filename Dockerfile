FROM python:3.12-slim AS builder
ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /build
COPY requirements.txt .
RUN python -m venv /opt/venv && /opt/venv/bin/pip install -r requirements.txt

FROM python:3.12-slim AS runtime
ENV PATH="/opt/venv/bin:$PATH" PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
RUN useradd --system --no-create-home --uid 10001 aplikasi
WORKDIR /srv/app
COPY --from=builder /opt/venv /opt/venv
COPY app ./app
COPY static ./static
COPY wsgi.py entrypoint.sh ./
RUN sed -i 's/\r$//' entrypoint.sh && chmod +x entrypoint.sh
USER aplikasi
EXPOSE 3000
ENTRYPOINT ["./entrypoint.sh"]
