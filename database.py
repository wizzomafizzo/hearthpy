# hearthpy database

import time
import json
import sqlite3
from datetime import datetime
from datetime import timedelta

import config

db = sqlite3.connect(config.db_filename,
                     detect_types=sqlite3.PARSE_DECLTYPES,
                     check_same_thread=False)

def now():
    return datetime.now()

def start_of_today():
    today = datetime.now()
    return datetime(today.year, today.month, today.day)

def end_of_today():
    today = datetime.now()
    return datetime(today.year, today.month, today.day, 23, 59, 59)

def start_of_month():
    today = datetime.now()
    return datetime(today.year, today.month, 1)

def a_day_ago():
    today = datetime.now()
    return today - timedelta(1)

def a_week_ago():
    today = datetime.now()
    return today - timedelta(7)

def a_month_ago():
    today = datetime.now()
    return today - timedelta(31)

def decks_shown_date():
    today = datetime.now()
    return today - timedelta(config.decks_shown)

def read_date(date):
    return datetime(*time.strptime(date, "%d/%m/%Y")[0:6])

def end_of_day(date):
    return date + timedelta(hours=23, minutes=59)

def winrate(total, wins):
    if wins == 0 or total == 0:
        return 0
    else:
        return (wins * 100) / total

def import_old_matches(db, export_filename):
    system_epoch = datetime.date(*time.gmtime(0)[0:3])
    ntp_epoch = datetime.date(1900, 1, 1)
    ntp_delta = (system_epoch - ntp_epoch).days * 24 * 3600
    matches = json.load(open(export_filename))
    q = "insert into matches values (?, ? ,?, ?, ?, ?)"
    c = db.cursor()
    total = 0
    for x in matches:
        date = datetime.fromtimestamp(x[1] - ntp_delta)
        c.execute(q, (date, x[2], x[3], x[4], x[5], x[6]))
        total += 1
    db.commit()
    return total


class Matches():
    def __init__(self, db):
        self.db = db

    def init_db(self):
        q = ("create table if not exists matches "
             "(date timestamp, mode text, deck text, "
             "opponent text, notes text, outcome integer)")
        c = self.db.cursor()
        c.execute(q)
        self.db.commit()

    def add(self, mode, deck, opponent, notes, outcome):
        assert type(mode) is str
        assert mode in config.modes
        assert type(deck) is str
        assert type(opponent) is str
        assert opponent in config.heroes
        assert type(notes) is str
        assert type(outcome) is bool

        if outcome:
            outcome = 1
        else:
            outcome = 0

        q = "insert into matches values (?, ? ,?, ?, ?, ?)"
        c = self.db.cursor()
        c.execute(q, (datetime.now(),
                      mode,
                      deck,
                      opponent,
                      notes,
                      outcome))
        self.db.commit()
        return c.lastrowid

    def remove(self, match_id):
        q = "delete from matches where rowid = ?"
        c = self.db.cursor()
        c.execute(q, (match_id,))
        self.db.commit()
        return match_id

    def all(self):
        q = "select rowid,* from matches"
        c = self.db.cursor()
        c.execute(q)
        return c.fetchall()

    def get(self, match_id):
        q = "select rowid,* from matches where rowid = ?"
        c = self.db.cursor()
        c.execute(q, (match_id,))
        return c.fetchone()

    def read(self, match):
        if match[6] == 1:
            outcome = True
        else:
            outcome = False
        return {
            "id": match[0],
            "date": match[1],
            "mode": match[2],
            "deck": match[3],
            "opponent": match[4],
            "notes": match[5],
            "outcome": outcome
        }

    def backup(self):
        matches = self.all()
        backup = []
        for row in matches:
            match = self.read(row)
            match["date"] = str(match["date"])
            backup.append(match)
        return backup

    def import_backup(self, matches):
        q = "insert into matches values (?, ? ,?, ?, ?, ?)"
        c = self.db.cursor()
        total = 0
        for match in matches:
            match["date"] = datetime.strptime(match["date"],
                                              "%Y-%m-%d %H:%M:%S")
            c.execute(q, (match["date"], match["mode"], match["deck"],
                          match["opponent"], match["notes"], match["outcome"]))
            total += 1
        self.db.commit()
        return total

    def search(self, from_date=None, to_date=None,
               mode=None, deck=None, opponent=None,
               notes=None, outcome=None, limit=None):
        q = ("select rowid,* from matches where date between ? and ? "
             "and deck like ? and opponent like ? and notes like ? ")

        # from_date
        if from_date is None:
            from_date = datetime.min
        else:
            assert type(from_date) is datetime
        # to_date
        if to_date is None:
            to_date = datetime.now()
        else:
            assert type(to_date) is datetime
        # deck
        if deck is None:
            deck = "%"
        else:
            assert type(deck) is str
            deck = "%{}%".format(deck)
        # opponent
        if opponent is None:
            opponent = "%"
        else:
            assert type(opponent) is str
        # notes
        if notes is None:
            notes = "%"
        else:
            assert type(notes) is str
            notes = "%{}%".format(notes)
        # mode
        if mode is None:
            mode = "%"
            q += "and mode like ? "
        elif mode == "Ranked":
            mode = "Casual"
            q += "and mode != ? "
        else:
            assert type(mode) is str
            q += "and mode like ? "
        # outcome
        if outcome is not None:
            if outcome:
                q += "and outcome = 1 "
            else:
                q += "and outcome = 0 "

        args = [from_date, to_date, deck, opponent, notes, mode]

        q += "order by date desc"

        if limit is not None:
             q += " limit ?"
             args.append(limit)

        c = self.db.cursor()
        c.execute(q, args)

        return [self.read(x) for x in c.fetchall()]

    def decks(self, from_date=None):
        q = ("select distinct deck from matches "
             "where date > ? order by deck desc")
        if from_date is None:
            from_date = datetime.min
        else:
            assert type(from_date) is datetime
        c = self.db.cursor()
        c.execute(q, (from_date,))
        return [x[0] for x in c.fetchall()]

    def total(self):
        q = "select count(*) from matches"
        c = self.db.cursor()
        c.execute(q)
        return c.fetchone()[0]

    def total_in_range(self, from_date, to_date):
        q = ("select count(*) from matches "
             "where date between ? and ?")
        if from_date is None:
            from_date = datetime.min
        if to_date is None:
            to_date = now()
        c = self.db.cursor()
        c.execute(q, (from_date, to_date))
        return c.fetchone()[0]

    def stats(self, matches):
        total = len(matches)
        wins = len([x for x in matches if x["outcome"]])
        losses = total - wins
        return {
            "total": total,
            "wins": wins,
            "losses": losses,
            "winrate": winrate(total, wins)
        }

    def deck_stats(self, from_date):
        names = sorted(self.decks(from_date))
        decks = []
        for x in names:
            stats = self.stats(self.search(deck=x))
            stats["deck"] = x
            decks.append(stats)
        return decks

    def rename_deck(self, old, new):
        q = "update matches set deck = ? where deck = ?"
        c = self.db.cursor()
        c.execute(q, (new, old))
        self.db.commit()

    def remove_deck(self, name):
        q = "delete from matches where deck = ?"
        c = self.db.cursor()
        c.execute(q, (name,))
        self.db.commit()

    def daily_stats(self, days, deck=None):
        start = start_of_today()
        end = end_of_today()
        daily = []
        for x in range(days):
            delta = timedelta(x)
            matches = self.search(start - delta, end - delta)
            stats = self.stats(matches)
            stats["date"] = start - delta
            daily.append(stats)
        return daily

    def opponent_stats(self, matches):
        opponents = {}
        for x in config.heroes:
            filtered = [y for y in matches if y["opponent"] == x]
            opponents[x] = self.stats(filtered)
        return opponents

    def current_rank(self):
        matches = self.search(start_of_month(), mode="Ranked")
        if len(matches) == 0:
            return config.modes[len(config.modes) - 2]
        return matches[0]["mode"]

    def last_mode(self):
        q = "select rowid,* from matches order by rowid desc limit 1"
        c = self.db.cursor()
        c.execute(q)
        match = c.fetchone()
        if match is None:
            return config.modes[len(config.modes) - 1]
        else:
            return self.read(match)["mode"]

    def best_rank(self):
        q = "select distinct mode from matches"
        c = self.db.cursor()
        c.execute(q)
        results = c.fetchall()

        if len(results) == 0:
            return "None"

        modes = [x[0] for x in results]

        if "Legend" in modes:
            return "Legend"

        ranks = [int(x[5:]) for x in modes
                 if x.startswith("Rank")]

        return "Rank " + str(sorted(ranks)[0])

    def heroes_played(self):
        matches = self.search()
        heroes_tally = {}
        for x in config.heroes_abbrv.keys():
            heroes_tally[x] = 0

        for x in matches:
            hero = x["deck"][0:2]
            heroes_tally[hero] += 1

        heroes = [(config.heroes_abbrv[x], heroes_tally[x])
                  for x in heroes_tally.keys()]

        return sorted(heroes, key=lambda x: x[1], reverse=True)

    def guest_stats(self):
        stats = {}
        deck_game_min = 20
        matches = self.search()

        if len(matches) == 0:
            return False

        deck_stats = self.deck_stats(None)
        heroes_played = self.heroes_played()
        opponent_stats = self.opponent_stats(matches)
        opponents = []
        for x in opponent_stats.keys():
            opponents.append((x, opponent_stats[x]["total"],
                              opponent_stats[x]["winrate"]))

        deck_total = sorted([(x["deck"], x["total"]) for x in deck_stats],
                            key=lambda x: x[1], reverse=True)
        deck_winrate = sorted([(x["deck"], x["winrate"]) for x in deck_stats
                               if x["total"] > deck_game_min],
                              key=lambda x: x[1], reverse=True)
        opponent_total = sorted(opponents, key=lambda x: x[1], reverse=True)
        opponent_winrate = sorted(opponents, key=lambda x: x[2], reverse=True)

        stats["most_played_deck"] = deck_total[0]
        stats["best_deck"] = deck_winrate[0]
        stats["worst_deck"] = deck_winrate[-1]
        stats["most_seen_class"] = (opponent_total[0][0], opponent_total[0][1])
        stats["least_seen_class"] = (opponent_total[-1][0], opponent_total[-1][1])
        stats["best_seen_class"] = (opponent_winrate[0][0], opponent_winrate[0][2])
        stats["worst_seen_class"] = (opponent_winrate[-1][0], opponent_winrate[-1][2])
        stats["best_rank"] = self.best_rank()
        stats["most_played_class"] = heroes_played[0]
        stats["least_played_class"] = heroes_played[-1]

        return stats


class Cards():
    def __init__(self, db):
        self.db = db

    def init_db(self):
        cards = ("create table if not exists cards "
                 "(card_id text, name text, card_text text, rarity text, "
                 "type text, cost integer, attack integer, health integer, "
                 "card_set text, race text, artist text, flavor text, "
                 "mechanics text, class text)")
        collection = ("create table if not exists collection "
                      "(card_id text, owned integer, notes text)")
        no_dupes = ("create unique index if not exists no_dupes "
                    "on collection (card_id)")
        c = self.db.cursor()
        c.execute(cards)
        c.execute(collection)
        c.execute(no_dupes)
        self.db.commit()

    def add(self, card_json):
        # TODO: skip duplicates?
        q = ("insert into cards values (?, ?, ?, ?, ?, "
             "?, ?, ?, ?, ?, ?, ?, ?, ?)")
        c = self.db.cursor()

        # race
        if "race" in card_json:
            race = card_json["race"]
        else:
            race = ""
        # mechanics
        if "mechanics" in card_json:
            mechanics = ",".join(card_json["mechanics"])
        else:
            mechanics = ""
        # class
        if "playerClass" in card_json:
            player_class = card_json["playerClass"]
        else:
            player_class = "NEUTRAL"
        # attack
        if "attack" in card_json:
            attack = card_json["attack"]
        else:
            attack = -1
        # health
        if "health" in card_json:
            health = card_json["health"]
        else:
            health = -1
        # text
        if "text" in card_json:
            text = card_json["text"]
        else:
            text = ""
        # cost
        if "cost" in card_json:
            cost = card_json["cost"]
        else:
            cost = -1
        # artist
        if "artist" in card_json:
            artist = card_json["artist"]
        else:
            artist = ""
        # flavor
        if "flavor" in card_json:
            flavor = card_json["flavor"]
        else:
            flavor = ""

        c.execute(q, (card_json["id"], card_json["name"],
                      text, card_json["rarity"], card_json["type"],
                      cost, attack, health, card_json["set"],
                      race, artist, flavor, mechanics, player_class))
        self.db.commit()
        return c.lastrowid

    def add_collection(self, card_id):
        q = "insert into collection values (?, ?, ?)"
        c = self.db.cursor()
        c.execute(q, (card_id, 0, ""))
        self.db.commit()
        return c.lastrowid

    def owned(self, card_id):
        q = "select owned from collection where card_id = ?"
        c = self.db.cursor()
        c.execute(q, (card_id,))
        total = c.fetchone()
        if total is None:
            return
        else:
            return total[0]

    def add_owned(self, card_id):
        owned = self.owned(card_id)
        if owned is None:
            return
        card = self.read(self.get(card_id))
        if card["rarity"] == "LEGENDARY":
            max_owned = 1
        else:
            max_owned = 2
        if owned < max_owned:
            owned += 1
        q = "update collection set owned = ? where card_id = ?"
        c = self.db.cursor()
        c.execute(q, (owned, card_id))
        self.db.commit()
        return owned

    def remove_owned(self, card_id):
        owned = self.owned(card_id)
        if owned is None:
            return
        if owned > 0:
            owned -= 1
        q = "update collection set owned = ? where card_id = ?"
        c = self.db.cursor()
        c.execute(q, (owned, card_id))
        self.db.commit()
        return owned

    def set_notes(self, card_id, notes):
        q = "update collection set notes = ? where card_id = ?"
        c = self.db.cursor()
        c.execute(q, (notes, card_id))
        self.db.commit()
        return notes

    def import_cards(self, filename):
        cards = json.load(open(filename, encoding="utf-8"))
        imported = []
        total = 0
        c = self.db.cursor()
        c.execute("drop table cards")
        self.db.commit()
        self.init_db()
        for x in cards:
            valid = (x["id"] not in imported and
                     x["type"] != "HERO")
            if valid:
                self.add(x)
                try:
                    self.add_collection(x["id"])
                except sqlite3.IntegrityError:
                    pass
                total += 1
                imported.append(x["id"])
        return total

    def all_cards(self):
        q = "select rowid,* from cards"
        c = self.db.cursor()
        c.execute(q)
        return c.fetchall()

    def all_collection(self):
        q = "select rowid,* from collection"
        c = self.db.cursor()
        c.execute(q)
        return c.fetchall()

    def total(self):
        q = "select count(*) from cards"
        c = self.db.cursor()
        c.execute(q)
        return c.fetchone()[0]

    def get(self, card_id):
        q = ("select * from cards "
             "left join collection on cards.card_id = collection.card_id "
             "where cards.card_id = ?")
        c = self.db.cursor()
        c.execute(q, (card_id,))
        return c.fetchone()

    def read(self, card):
        mechanics = card[12].split(",")
        if mechanics[0] == "":
            mechanics = ["NONE"]
        text = card[2]
        if text == "":
            text = "None"
        return {
            "id": card[0],
            "name": card[1],
            "text": text,
            "rarity": card[3],
            "type": card[4],
            "cost": card[5],
            "attack": card[6],
            "health": card[7],
            "set": card[8],
            "race": card[9],
            "artist": card[10],
            "flavor": card[11],
            "mechanics": mechanics,
            "class": card[13],
            "owned": card[15],
            "notes": card[16]
        }

    def backup_collection(self):
        collection = self.all_collection()
        backup = []
        for row in collection:
            card = {}
            card["card_id"] = row[1]
            card["owned"] = row[2]
            card["notes"] = row[3]
            backup.append(card)
        return backup

    def import_collection_backup(self, collection):
        q = "insert into collection values (?, ?, ?)"
        c = self.db.cursor()
        added = 0
        skipped = 0
        for card in collection:
            try:
                c.execute(q, (card["card_id"],
                              card["owned"],
                              card["notes"]))
                added += 1
            except sqlite3.IntegrityError:
                skipped += 1
        self.db.commit()
        return [added, skipped]

    def search(self, name=None, text=None, rarity=None,
               card_type=None, cost=None, attack=None,
               health=None, card_set=None, mechanics=None,
               hero=None, owned=None, limit=None, offset=None):
        if name is None:
            name = "%"
        else:
            assert type(name) is str
            name = "%{}%".format(name)

        if text is None:
            text = "%"
        else:
            assert type(text) is str
            text = "%{}%".format(text)

        if rarity is None:
            rarity = "%"
        else:
            assert type(rarity) is str

        if card_type is None:
            card_type = "%"
        else:
            assert type(card_type) is str

        if card_set is None:
            card_set = "%"
        else:
            assert type(card_set) is str

        if mechanics is None:
            mechanics = "%"
        else:
            assert type(mechanics) is str
            mechanics = "%{}%".format(mechanics)

        if hero is None:
            hero = "%"
        else:
            assert type(hero) is str

        q = ("select * from cards "
             "left join collection on cards.card_id = collection.card_id "
             "where name like ? and card_text like ? "
             "and rarity like ? and type like ? and card_set like ? "
             "and mechanics like ? and class like? ")

        args = [name, text, rarity, card_type, card_set, mechanics, hero]

        if cost is not None:
            assert type(cost) is int
            q += "and cost = ? "
            args.append(cost)

        if attack is not None:
            assert type(attack) is int
            q += "and attack = ? "
            args.append(attack)

        if health is not None:
            assert type(health) is int
            q += "and health = ? "
            args.append(health)

        if owned is not None:
            assert type(owned) is int
            q += "and owned = ? "
            args.append(owned)

        q += "order by class, cost, name"

        if limit is not None:
            assert type(limit) is int
            q += " limit ?"
            args.append(limit)

        if offset is not None:
            assert type(offset) is int
            q += " offset ?"
            args.append(offset)

        c = self.db.cursor()
        c.execute(q, args)
        return [self.read(x) for x in c.fetchall()]

    def rarities(self):
        c = self.db.cursor()
        q = "select distinct rarity from cards order by rarity"
        c.execute(q)
        return [x[0] for x in c.fetchall()]

    def sets(self):
        c = self.db.cursor()
        q = "select distinct card_set from cards order by card_set"
        c.execute(q)
        return [x[0] for x in c.fetchall()]

    def types(self):
        c = self.db.cursor()
        q = "select distinct type from cards"
        c.execute(q)
        return [x[0] for x in c.fetchall()]

    def missing(self):
        q = ("select * from cards left join collection "
             "on cards.card_id = collection.card_id where "
             "owned < 2 order by class, cost, name")
        c = self.db.cursor()
        c.execute(q)
        cards = c.fetchall()
        cards = [self.read(x) for x in cards]
        missing = []
        total = 0
        for card in cards:
            if card["rarity"] == "LEGENDARY" and card["owned"] == 1:
                continue
            total += 2 - card["owned"]
            missing.append(card)
        return (missing, total)

    def dust_needed(self):
        missing_cards = self.missing()[0]
        packs = config.card_packs
        craft_cost = config.craft_cost
        dust_needed = {}
        for pack in packs:
            dust_needed[pack] = 0
        for card in missing_cards:
            if card["set"] in packs:
                cost = craft_cost[card["rarity"]] * (2 - card["owned"])
                dust_needed[card["set"]] += cost
        return dust_needed
