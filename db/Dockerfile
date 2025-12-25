FROM postgres:15-alpine

# Set environment variables
ENV POSTGRES_USER=postgres
ENV POSTGRES_PASSWORD=postgres
ENV POSTGRES_DB=pokedraft

# Copy initialization scripts and set permissions
COPY --chmod=755 init/ /docker-entrypoint-initdb.d/

# Expose PostgreSQL port
EXPOSE 5432

# Health check
HEALTHCHECK --interval=10s --timeout=5s --start-period=10s --retries=5 \
  CMD pg_isready -U postgres -d pokedraft || exit 1
