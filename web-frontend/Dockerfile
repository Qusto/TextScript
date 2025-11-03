# AICODE-NOTE: T056 - Multi-stage Dockerfile for Next.js 14 frontend
# Targets node:20-alpine for minimal image size (~100MB vs ~1GB with full node)
# Three stages: deps (install dependencies), builder (build app), runner (production)

# Stage 1: Install dependencies
# AICODE-NOTE: Separate stage for dependencies to leverage Docker layer caching
# If package.json hasn't changed, this layer is reused (faster builds)
FROM node:20-alpine AS deps
WORKDIR /app

# AICODE-NOTE: Copy only package files first for better caching
# If source code changes but package.json doesn't, deps layer is reused
COPY package.json package-lock.json ./

# AICODE-NOTE: Clear npm proxy settings to avoid connection issues
RUN npm config delete proxy || true && \
    npm config delete https-proxy || true && \
    npm config delete http-proxy || true

# AICODE-NOTE: Install all dependencies (including dev) for build stage
RUN npm ci

# Stage 2: Build the application
# AICODE-NOTE: Builder stage compiles TypeScript and creates production build
FROM node:20-alpine AS builder
WORKDIR /app

# AICODE-NOTE: Copy deps from previous stage to avoid reinstalling
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# AICODE-NOTE: Next.js telemetry disabled for privacy and faster builds
ENV NEXT_TELEMETRY_DISABLED=1

# AICODE-NOTE: Build Next.js app - outputs to .next directory
RUN npm run build

# Stage 3: Production runtime
# AICODE-NOTE: Final minimal image with only runtime dependencies
FROM node:20-alpine AS runner
WORKDIR /app

# AICODE-NOTE: Run as non-root user for security (principle of least privilege)
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# AICODE-NOTE: Copy only necessary files for runtime (not source code)
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

# AICODE-NOTE: Set ownership to nextjs user for security
RUN chown -R nextjs:nodejs /app

USER nextjs

# AICODE-NOTE: Expose port 3000 (Next.js default)
EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"
ENV NEXT_TELEMETRY_DISABLED=1

# AICODE-NOTE: Start Next.js server using standalone output
# Standalone mode bundles all dependencies (node_modules) into .next/standalone
CMD ["node", "server.js"]
