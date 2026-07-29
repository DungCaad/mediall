from .settings import *  # noqa: F403


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# The production account history contains MySQL-only SQL; tests build its current
# model state directly so the isolated SQLite database stays portable.
MIGRATION_MODULES = {
    "accounts": None,
    "doctors": None,
}
