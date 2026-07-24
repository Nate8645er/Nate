"""Kontrolliertes Migrieren: `python -m app.migrate`."""
from .db import migrate

if __name__ == "__main__":
    migrate()
    print("Migrationen angewendet.")
