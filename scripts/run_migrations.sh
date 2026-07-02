set -e

# Upgrade DB
docker exec -it api alembic upgrade head
