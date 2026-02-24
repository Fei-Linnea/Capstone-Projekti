FROM node:20-alpine

WORKDIR /app

# Install dependencies
COPY pipeline/web/frontend/package.json pipeline/web/frontend/package-lock.json ./
RUN npm ci

# Copy source
COPY pipeline/web/frontend/ .

# Next.js dev server with API proxy env var
ENV NEXT_PUBLIC_API_URL=http://backend:5000
ENV HOSTNAME=0.0.0.0

EXPOSE 3000

CMD ["npm", "run", "dev"]
