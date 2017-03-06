#!/usr/bin/env python3

import pickle
import os
import sys
import json
import datetime
import urllib.request

import config
import web
import database
from web import app


def get_credentials():
    try:
        fp = open(config.auth_filename, "rb")
        credentials = pickle.load(fp)
    except FileNotFoundError:
        return False
    return credentials


def setup_credentials():
    credentials = {}
    print("Setting up login credentials")
    username = input("Username: ")
    password = input("Password: ")
    print("Generating secret key...")
    secret_key = os.urandom(24)
    credentials["username"] = username
    credentials["password"] = password
    credentials["secret_key"] = secret_key
    fp = open(config.auth_filename, "wb")
    pickle.dump(credentials, fp)
    print("Credentials stored in: {}".format(config.auth_filename))


def setup_database():
    print("Setting up database")
    db = database.db
    m = database.Matches(db)
    c = database.Cards(db)
    print("Setting up matches table")
    m.init_db()
    print("Setting up cards table")
    c.init_db()
    print("Database setup complete")


def backup_database():
    print("Backing up database")
    db = database.db
    m = database.Matches(db)
    c = database.Cards(db)
    matches = m.backup()
    collection = c.backup_collection()
    now = datetime.datetime.now()
    timestamp = int(now.timestamp())
    matches_filename = "data/matches-{}.json".format(timestamp)
    collection_filename = "data/collection-{}.json".format(timestamp)
    json.dump(matches, open(matches_filename, "w", encoding="utf-8"))
    print("Backed up matches: {}".format(matches_filename))
    json.dump(collection, open(collection_filename, "w", encoding="utf-8"))
    print("Backed up collection: {}".format(collection_filename))
    print("Database backup complete")


def import_matches(filename):
    print("Importing matches backup")
    fp = open(filename, encoding="utf-8")
    db = database.db
    m = database.Matches(db)
    matches = json.load(fp)
    imported = m.import_backup(matches)
    print("Imported {} matches".format(imported))


def import_collection(filename):
    print("Importing collection backup")
    fp = open(filename, encoding="utf-8")
    db = database.db
    c = database.Cards(db)
    cards = json.load(fp)
    imported = c.import_collection_backup(cards)
    print("Imported {} cards, skipped {}".format(imported[0],
                                                 imported[1]))


def import_old_matches(filename):
    print("Importing old matches backup")
    imported = database.import_old_matches(filename)
    print("Imported {} matches".format(imported))


def update_cards():
    if os.path.isfile("data/cards.json"):
        print("Moving old cards dump")
        now = datetime.datetime.now()
        timestamp = int(now.timestamp())
        os.rename("data/cards.json", "data/cards-{}.json".format(timestamp))
    print("Downloading cards json dump")
    request = urllib.request.Request(
        config.cards_json_url, data=None,
        headers={ "User-Agent": config.cards_json_agent }
    )
    cards_json = urllib.request.urlopen(request)
    cards_file = open("data/cards.json", "w")
    cards_file.write(cards_json.read().decode("utf-8"))
    print("Importing cards")
    c = database.Cards(database.db)
    imported = c.import_cards("data/cards.json")
    print("Imported {} cards".format(imported))


def setup():
    setup_credentials()
    setup_database()


def run():
    credentials = get_credentials()
    if not credentials or not os.path.isfile(config.db_filename):
        print("hearthpy has not been configured")
        exit(1)

    web.credentials = credentials
    web.app.secret_key = credentials["secret_key"]
    web.app.run(port=config.port, debug=True)


def show_help():
    print("Commands:")
    print("run, setup, backup, update_cards,"
          " import_matches, import_collection")


credentials = get_credentials()
if credentials:
    web.credentials = credentials
    app.secret_key = credentials["secret_key"]

if __name__ == "__main__":
    if len(sys.argv) < 2:
        show_help()
        exit(0)

    command = sys.argv[1]
    if command == "run":
        run()
    elif command == "setup":
        setup()
    elif command == "backup":
        backup_database()
    elif command == "update_cards":
        update_cards()
    elif command == "import_matches" and len(sys.argv) == 3:
        import_matches(sys.argv[2])
    elif command == "import_collection":
        import_collection(sys.argv[2])
    elif command == "import_old_matches" and len(sys.argv) == 3:
        import_old_matches(sys.argv[2])
    else:
        show_help()
