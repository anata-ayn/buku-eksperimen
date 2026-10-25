import os

from .db import database_from_env
from .seed import pasang_contoh


def main():
    database = database_from_env()
    database.wait_until_ready()
    database.create_schema()
    if os.environ.get("RUN_SEED", "false").lower() == "true":
        if pasang_contoh(database):
            print("Data contoh Modul 2A dipasang.")
        else:
            print("Data sudah ada, seed dilewati.")


if __name__ == "__main__":
    main()
