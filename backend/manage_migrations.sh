#!/usr/bin/env bash
set -euo pipefail

# Helper to run alembic commands inside the backend container or locally when working directory is backend/
# Usage:
#   ./manage_migrations.sh revision --autogenerate -m "initial migration"
#   ./manage_migrations.sh upgrade head

CMD="$@"

if [ -t 1 ] && [ -f /.dockerenv ]; then
  # inside container
  alembic "$@"
else
  (cd backend && alembic "$@")
fi
