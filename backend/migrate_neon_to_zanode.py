"""
Migrate the Neon staging database to a Zanode-managed PostgreSQL database.

Reads connection strings from environment variables or a local `.env.zanode-migration` file.
Never commit `.env.zanode-migration` — it is gitignored by default.

Steps:
1. pg_dump from Neon (excluding derived Wagtail tables).
2. Drop/recreate the `public` schema on Zanode.
3. Restore the dump.
4. Run Django migrations.
5. Bootstrap Wagtail.
6. Rebuild the Wagtail search index.
"""
import os
import subprocess
import sys
import tempfile
import urllib.parse
from pathlib import Path

REQUIRED_BINARIES = ["pg_dump", "psql"]

# Common PostgreSQL client binary locations on Windows.
COMMON_PG_DIRS = [
    r"C:\Program Files\PostgreSQL\18\bin",
    r"C:\Program Files\PostgreSQL\17\bin",
    r"C:\Program Files\PostgreSQL\16\bin",
    r"C:\Program Files\PostgreSQL\15\bin",
    r"C:\Program Files\PostgreSQL\14\bin",
    r"C:\Program Files\PostgreSQL\13\bin",
]

# Wagtail tables that are derived/indexed and should not have their rows copied.
# We keep the table definitions so migrations stay consistent, then rebuild the indexes.
EXCLUDED_DATA_TABLES = [
    "wagtailsearch_indexentry",
    "wagtailcore_referenceindex",
]


PG_BIN_PATHS = {}


def find_binary(name: str) -> str | None:
    # Check PATH first.
    for path_dir in os.environ.get("PATH", "").split(os.pathsep):
        candidate = Path(path_dir) / (name + ".exe" if sys.platform == "win32" else name)
        if candidate.exists():
            return str(candidate)
    # Check common PostgreSQL installation directories.
    for pg_dir in COMMON_PG_DIRS:
        candidate = Path(pg_dir) / (name + ".exe" if sys.platform == "win32" else name)
        if candidate.exists():
            return str(candidate)
    return None


def check_binaries():
    missing = []
    for binary in REQUIRED_BINARIES:
        path = find_binary(binary)
        if path:
            PG_BIN_PATHS[binary] = path
        else:
            missing.append(binary)
    if missing:
        print(f"Missing required binaries: {', '.join(missing)}")
        print("Install PostgreSQL client tools: https://www.postgresql.org/download/")
        sys.exit(1)
    print(f"Using pg_dump: {PG_BIN_PATHS['pg_dump']}")
    print(f"Using psql: {PG_BIN_PATHS['psql']}")


def load_env_file(path: Path):
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        if line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if key in os.environ:
            continue
        os.environ[key] = value.strip().strip('"').strip("'")


def get_url(*keys: str) -> str:
    for key in keys:
        value = os.environ.get(key, "").strip()
        if value:
            return normalize_url(value)
    print(f"Error: none of {', '.join(keys)} are set in environment or .env.zanode-migration")
    sys.exit(1)


def normalize_url(url: str) -> str:
    """Strip connection-string parameters that common tools do not support."""
    if "sslnegotiation=" not in url:
        return url
    parsed = urllib.parse.urlparse(url)
    query = urllib.parse.parse_qs(parsed.query)
    query.pop("sslnegotiation", None)
    new_query = urllib.parse.urlencode(query, doseq=True)
    return urllib.parse.urlunparse(parsed._replace(query=new_query))


def host_from_url(url: str) -> str:
    return urllib.parse.urlparse(url).hostname or "unknown"


def redact_url(value: str) -> str:
    if "://" not in value:
        return value
    parsed = urllib.parse.urlparse(value)
    if parsed.password:
        return value.replace(f":{parsed.password}@", ":***@", 1)
    return value


def redact_command(args: list[str]) -> str:
    return " ".join(redact_url(arg) for arg in args)


def run(args: list[str], env: dict | None = None, check: bool = True):
    print(f"$ {redact_command(args)}")
    return subprocess.run(args, env=env, check=check)


def main():
    check_binaries()
    load_env_file(Path(".env.zanode-migration"))

    # SOURCE_DATABASE_URL is explicit; otherwise fall back to the current Vercel DATABASE_URL.
    source_url = get_url("SOURCE_DATABASE_URL", "DATABASE_URL")
    target_url = get_url("TARGET_DATABASE_URL")

    print(f"Source host: {host_from_url(source_url)}")
    print(f"Target host: {host_from_url(target_url)}")

    if host_from_url(source_url) == host_from_url(target_url):
        print("Error: source and target hosts are the same. Aborting.")
        sys.exit(1)

    with tempfile.NamedTemporaryFile(suffix=".sql", delete=False, mode="w") as f:
        dump_path = f.name

    try:
        # 1. Dump from Neon, excluding data in derived Wagtail tables.
        exclude_args = []
        for table in EXCLUDED_DATA_TABLES:
            exclude_args.extend(["--exclude-table-data", table])

        dump_cmd = [
            PG_BIN_PATHS["pg_dump"],
            "--no-owner",
            "--no-privileges",
            "--no-comments",
            "--verbose",
            source_url,
            *exclude_args,
            "-f",
            dump_path,
        ]
        run(dump_cmd)
        print(f"Dump written to {dump_path}")

        # 2. Clean the target schema.
        print("Cleaning target public schema...")
        run([
            PG_BIN_PATHS["psql"],
            target_url,
            "-c",
            "DROP SCHEMA IF EXISTS public CASCADE; CREATE SCHEMA public;",
        ])

        # 3. Restore the dump.
        print("Restoring dump to Zanode...")
        run([PG_BIN_PATHS["psql"], target_url, "-f", dump_path])

        # 4. Run Django migrations against the target database.
        print("Running Django migrations...")
        env = os.environ.copy()
        env["DATABASE_URL"] = target_url
        run([sys.executable, "manage.py", "migrate", "--run-syncdb"], env=env)

        # 5. Bootstrap Wagtail.
        print("Bootstrapping Wagtail...")
        run([sys.executable, "setup_wagtail.py"], env=env)

        # 6. Rebuild search index.
        print("Rebuilding Wagtail search index...")
        run([sys.executable, "manage.py", "update_index"], env=env)

        print("\nMigration complete.")
        print(f"Target database is ready at {host_from_url(target_url)}")

    finally:
        Path(dump_path).unlink(missing_ok=True)


if __name__ == "__main__":
    main()
