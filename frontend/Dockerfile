FROM node:20-bookworm-slim AS builder

WORKDIR /workspace/frontend
ENV NEXT_TELEMETRY_DISABLED=1
ARG NEXT_PUBLIC_API_BASE_URL=/api/v1
ENV NEXT_PUBLIC_API_BASE_URL=${NEXT_PUBLIC_API_BASE_URL}

RUN apt-get update \
  && apt-get install -y --no-install-recommends python3 \
  && rm -rf /var/lib/apt/lists/*

COPY frontend/package.json frontend/package-lock.json ./
COPY frontend/prisma ./prisma
COPY frontend/scripts ./scripts
RUN npm ci

COPY frontend/ ./
COPY infrastructure ../infrastructure
COPY security ../security
RUN npm run build

FROM node:20-bookworm-slim

WORKDIR /app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV NEXT_PUBLIC_API_BASE_URL=/api/v1

COPY --from=builder /workspace/frontend/package.json /workspace/frontend/package-lock.json ./
COPY --from=builder /workspace/frontend/node_modules ./node_modules
COPY --from=builder /workspace/frontend/.next ./.next
COPY --from=builder /workspace/frontend/public ./public
COPY --from=builder /workspace/frontend/next.config.ts ./next.config.ts

CMD ["sh", "-lc", "node_modules/.bin/next start -p 3010 -H 0.0.0.0"]
