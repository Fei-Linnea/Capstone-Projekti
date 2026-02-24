# ── Stage 1: Build ────────────────────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app

COPY pipeline/web/frontend/package.json pipeline/web/frontend/package-lock.json ./
RUN npm ci

COPY pipeline/web/frontend/ .

# Set the API URL at build time so it's baked into the static JS bundle
ENV NEXT_PUBLIC_API_URL=http://localhost:5000

RUN npm run build

# ── Stage 2: Serve static files with a tiny HTTP server ───────────────
FROM node:20-alpine

WORKDIR /app

RUN npm install -g serve@14

# Copy the static export from the builder
COPY --from=builder /app/out ./out

EXPOSE 3000

# serve -s = single-page-app mode (rewrites all routes to index.html)
CMD ["serve", "-s", "out", "-l", "3000"]
