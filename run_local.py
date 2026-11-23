"""Start the local Flask app and the project MySQL instance."""
import argparse
import importlib.util
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent
WORK = ROOT.parents[1]
LOCAL = ROOT / ".local"
DEFAULT_MYSQL = Path("C:/Program Files/MySQL/MySQL Server 8.0/bin")


def python_with_dependencies():
    if importlib.util.find_spec("flask") and importlib.util.find_spec("pymysql") and importlib.util.find_spec("bcrypt"):
        return
    candidates = [
        ROOT / ".venv" / "Scripts" / "python.exe",
        ROOT / ".venv" / "bin" / "python",
        WORK / "flask-venv" / "Scripts" / "python.exe",
    ]
    for candidate in candidates:
        if candidate.is_file() and candidate.resolve() != Path(sys.executable).resolve():
            raise SystemExit(subprocess.call([str(candidate), __file__, *sys.argv[1:]]))
    raise SystemExit("Install the dependencies with python -m pip install -r requirements.txt.")


def mysql_program(name):
    bin_dir = Path(os.getenv("MYSQL_BIN", str(DEFAULT_MYSQL)))
    executable = name + (".exe" if os.name == "nt" else "")
    candidate = bin_dir / executable
    if candidate.is_file():
        return str(candidate)
    if found := shutil.which(executable):
        return found
    raise SystemExit(f"Could not find {executable}. Set MYSQL_BIN to the MySQL bin directory.")


def require_free_port(port, label):
    with socket.socket() as check:
        try:
            check.bind(("127.0.0.1", port))
        except OSError as error:
            raise SystemExit(f"{label} port {port} is unavailable. Stop the previous local stack and retry.") from error


def start_mysql(log):
    data = Path(os.environ["MYSQL_DATA_DIR"]).resolve()
    command = [mysql_program("mysqld"), "--no-defaults", f"--datadir={data}"]
    port = int(os.getenv("DB_PORT", "3307"))
    require_free_port(port, "MySQL")
    if not (data / "mysql.ibd").is_file():
        data.mkdir(parents=True, exist_ok=True)
        result = subprocess.run([*command, "--initialize-insecure", "--console"], stdout=log, stderr=log)
        if result.returncode:
            raise SystemExit(f"MySQL initialization failed. See {log.name}.")
    return subprocess.Popen(
        [*command, "--bind-address=127.0.0.1", f"--port={port}", "--mysqlx=OFF", "--skip-log-bin", "--console"],
        stdout=log, stderr=log,
        creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--external-mysql", action="store_true", help="Use an already-running MySQL instance.")
    parser.add_argument("--port", type=int, default=5173, help="Flask web port.")
    args = parser.parse_args()
    python_with_dependencies()
    require_free_port(args.port, "Flask")

    import pymysql
    from app import app
    from db import connect
    from setup_database import prepare_database

    LOCAL.mkdir(exist_ok=True)
    previous_data = WORK / "mysql-local" / "data"
    default_data = previous_data if (previous_data / "mysql.ibd").exists() else LOCAL / "mysql-data"
    os.environ.setdefault("MYSQL_DATA_DIR", str(default_data))

    with (LOCAL / "mysql.log").open("a", encoding="utf-8") as log:
        server = None
        ready = False
        try:
            if not args.external_mysql:
                if os.getenv("DB_HOST", "127.0.0.1") != "127.0.0.1":
                    raise SystemExit("Use --external-mysql when connecting to a different database host.")
                server = start_mysql(log)
            for _ in range(60):
                if server is not None and server.poll() is not None:
                    raise SystemExit(f"MySQL stopped during startup. See {log.name}.")
                try:
                    with connect(database=False):
                        ready = True
                        break
                except pymysql.err.OperationalError as error:
                    if error.args[0] != 2003:
                        raise
                    time.sleep(1)
            if not ready:
                raise SystemExit(f"MySQL did not become ready. See {log.name}.")
            prepare_database()
            print(f"Food Management System: http://127.0.0.1:{args.port}", flush=True)
            app.run(host="127.0.0.1", port=args.port, debug=False, use_reloader=False)
        finally:
            if server is not None and server.poll() is None:
                if ready:
                    try:
                        with connect(database=False) as db, db.cursor() as cursor:
                            cursor.execute("SHUTDOWN")
                        server.wait(timeout=10)
                    except (pymysql.MySQLError, subprocess.TimeoutExpired):
                        pass
                if server.poll() is None:
                    server.terminate()
                    server.wait(timeout=10)


if __name__ == "__main__":
    main()
