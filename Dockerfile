FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .
COPY src/ src/

RUN pip install --no-cache-dir -e .

ENV MCP_TRANSPORT=sse
ENV MCP_API_KEY=""
ENV PORT=8000
ENV UPTIME_KUMA_URL=""
ENV UPTIME_KUMA_USERNAME=""
ENV UPTIME_KUMA_PASSWORD=""
ENV UPTIME_KUMA_TOKEN=""

EXPOSE 8000

CMD ["uptime-kuma-mcp-server"]
