# hearthpy web

import re
import sys
import urllib.parse
from functools import wraps

from flask import Flask
from flask import Response
from flask import request
from flask import render_template

from flask import session
from flask.json import dumps

import config

from database import db
from database import Cards
from database import Matches
from database import a_month_ago
from database import a_week_ago
from database import a_day_ago
from database import start_of_month
from database import read_date
from database import end_of_day
from database import winrate

app = Flask(__name__)

re_deck_name = re.compile(config.deck_template)
credentials = None

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "username" in session:
            return f(*args, **kwargs)
        else:
            return login()
    return decorated

def format_winrate(stats):
    if stats["winrate"] > config.winrate_tiers[1]:
        stats["label"] = "success"
    elif stats["winrate"] > config.winrate_tiers[0]:
        stats["label"] = "warning"
    else:
        stats["label"] = "danger"
    return stats

def format_opponents(stats):
    formatted = []
    for x in config.heroes:
        opponent = stats[x]
        opponent["opponent"] = x
        formatted.append(opponent)
    return sorted(formatted, key=lambda x: x["winrate"],
                  reverse=False)

def format_matches(matches):
    formatted = []
    for x in matches:
        if x["outcome"]:
            x["label"] = "success"
        else:
            x["label"] = "danger"
        formatted.append(x)
    return formatted

def opponent_ratios(opponents):
    total = sum([x["total"] for x in opponents.values()])
    ratios = []
    for x in opponents.keys():
        if total == 0:
            percentage = 0
        else:
            percentage = (opponents[x]["total"] * 100) / total
        ratios.append((x, percentage))
    return sorted(ratios, key=lambda x: x[1], reverse=True)

def hero_icon(stats):
    name = stats["deck"]
    short_hero = name[0:2]
    if short_hero in config.heroes_abbrv.keys():
        icon = config.heroes_abbrv[short_hero].lower()
    else:
        icon = "unknown"
    stats["hero_icon"] = icon
    return stats

def mode_icon(match):
    mode = match["mode"]
    match["mode_icon"] = mode.lower().replace(" ","")
    return match

def format_card(card):
    card["class"] = card["class"].title()
    card["type"] = card["type"].title()
    card["rarity"] = card["rarity"].title()
    card["mechanics"] = ", ".join([x.title() for x in card["mechanics"]])
    return card

def valid_deck_name(name):
    return re.match(re_deck_name, name)

def is_int(value):
  try:
    int(value)
    return True
  except ValueError:
    return False

def update_query_offset(query, offset):
    old_args = urllib.parse.parse_qsl(query)

    if old_args is None:
        return urllib.parse.urlencode([("offset", offset)])

    new_args = []
    updated = False
    for x in old_args:
        if x[0] == "offset":
            new_args.append(("offset", offset))
            updated = True
        else:
            new_args.append(x)

    if not updated:
        new_args.append(("offset", offset))

    return urllib.parse.urlencode(new_args)

@app.route("/", methods=["GET", "POST"])
def index():
    m = Matches(db)
    form_mode = False
    form_deck = False
    form_opponent = False
    last_added = False
    deck_exists = False
    submit_error = False

    # try submit a new match
    if request.method == "POST" and "username" in session:
        form_mode = request.form.get("mode", "")
        form_deck = request.form.get("deck", "")
        form_opponent = request.form.get("opponent", "")
        form_notes = request.form.get("notes", "")
        form_outcome = request.form.get("outcome", "")
        can_add = (form_mode != "" and
                   form_deck != "" and
                   form_opponent != "" and
                   form_outcome != "")
        if form_outcome == "win":
            outcome = True
        else:
            outcome = False

        if not can_add:
            submit_error = "Missing match values in form"
        elif not valid_deck_name(form_deck):
            submit_error = "Deck name does not match template"
        else:
            deck_exists = form_deck in m.decks()
            last_added = m.add(form_mode, form_deck,
                               form_opponent, form_notes,
                               outcome)

    active_mode = (form_mode or request.args.get("mode", ""))
    active_deck = (form_deck or request.args.get("deck", ""))
    active_opponent = (form_opponent or request.args.get("opponent", ""))

    if active_mode == "":
        active_mode = m.last_mode()

    if active_deck != "":
        deck = active_deck
    else:
        deck = None

    matches = [mode_icon(hero_icon(x)) for x in
               m.search(limit=config.front_match_limit, deck=deck)]
    deck_stats = [hero_icon(x) for x in m.deck_stats(a_month_ago())]
    season_stats = m.stats(m.search(start_of_month(), mode=["Ranked"]))
    overall_stats = [m.stats(m.search(a_day_ago(), deck=deck, limit=None)),
                     m.stats(m.search(a_week_ago(), deck=deck, limit=None)),
                     m.stats(m.search(a_month_ago(), deck=deck, limit=None)),
                     m.stats(m.search(deck=deck, limit=None))]

    opponent_stats = {
        "day": m.opponent_stats(m.search(a_day_ago(), deck=deck)),
        "week": m.opponent_stats(m.search(a_week_ago(), deck=deck)),
        "month": m.opponent_stats(m.search(a_month_ago(), deck=deck))
    }

    if "username" in session:
        gs = None
    else:
        gs = m.guest_stats()
        if gs:
            best_rank = mode_icon({"mode": gs["best_rank"]})
            most_played_deck = hero_icon({"deck": gs["most_played_deck"][0],
                                          "data": gs["most_played_deck"][1]})
            best_deck = hero_icon({"deck": gs["best_deck"][0],
                                   "data": gs["best_deck"][1]})
            worst_deck = hero_icon({"deck": gs["worst_deck"][0],
                                    "data": gs["worst_deck"][1]})
            gs["best_rank"] = best_rank
            gs["most_played_deck"] = most_played_deck
            gs["best_deck"] = best_deck
            gs["worst_deck"] = worst_deck

    args = {
        "modes": reversed(config.modes),
        "heroes": config.heroes,
        "deck_stats": [format_winrate(x) for x in deck_stats],
        "season_stats": format_winrate(season_stats),
        "season_rank": mode_icon({"mode": m.current_rank()}),
        "overall_stats": [format_winrate(x) for x in overall_stats],
        "opponent_stats": {
            "day": [format_winrate(x) for x in
                    format_opponents(opponent_stats["day"])],
            "week": [format_winrate(x) for x in
                     format_opponents(opponent_stats["week"])],
            "month": [format_winrate(x) for x in
                      format_opponents(opponent_stats["month"])]
        },
        "opponent_ratios": {
            "day": opponent_ratios(opponent_stats["day"]),
            "week": opponent_ratios(opponent_stats["week"]),
            "month": opponent_ratios(opponent_stats["month"])
        },
        "matches": format_matches(matches),
        "total_matches": len(matches),
        "total_decks": len(deck_stats),
        "active_mode": active_mode,
        "active_deck": active_deck,
        "active_opponent": active_opponent,
        "active_notes": request.args.get("notes", ""),
        "deck_exists": deck_exists,
        "submit_error": submit_error,
        "guest_stats": gs,
        "last_added": last_added
    }

    return render_template("hearthpy.html", **args)

@app.route("/remove")
@requires_auth
def remove_match():
    m = Matches(db)
    match_id = request.args.get("id", -1)
    match = m.get(match_id)
    if match is None:
        removed = False
    else:
        removed = True
        match = m.read(match)
        m.remove(match_id)
    return render_template("remove.html",
                           match_id=match_id,
                           match=match,
                           removed=removed)

@app.route("/matches")
def matches():
    m = Matches(db)

    from_date = request.args.get("from", "")
    to_date = request.args.get("to", "")
    deck = request.args.get("deck", "")
    notes = request.args.get("notes", "")
    outcome = request.args.get("outcome", "")
    offset = request.args.get("offset", "")

    opponent = request.args.getlist("opponent")
    mode = request.args.getlist("mode")

    search = {}

    if from_date != "":
        try:
            date = read_date(from_date)
            search["from_date"] = date
        except:
            search["from_date"] = None
    else:
        search["from_date"] = None

    if to_date != "":
        try:
            date = end_of_day(read_date(to_date))
            search["to_date"] = date
        except:
            search["to_date"] = None
    else:
        search["to_date"] = None

    if len(mode) > 0 and "All" not in mode:
        search["mode"] = mode

    if deck != "":
        search["deck"] = deck

    if len(opponent) > 0 and "All" not in opponent:
        search["opponent"] = opponent

    if notes != "":
        search["notes"] = notes

    if outcome == "win":
        search["outcome"] = True
    elif outcome == "lose":
        search["outcome"] = False

    matches = [mode_icon(hero_icon(x)) for x in format_matches(m.search(**search))]

    if len(matches) > 0:
        total = m.total_in_range(search["from_date"], search["to_date"])
    else:
        total = 0

    matches_found = len(matches)

    if offset != "" and is_int(offset):
        offset = int(offset)
    else:
        offset = 0

    prev_offset = offset - config.match_limit
    if prev_offset < 0:
        prev_offset = 0
    next_offset = offset + config.match_limit
    if next_offset > matches_found:
        next_offset = matches_found - config.match_limit

    query = request.query_string.decode()
    prev_url = update_query_offset(query, prev_offset)
    next_url = update_query_offset(query, next_offset)

    total_ratio = winrate(total, matches_found)
    stats = m.stats(matches)
    opponent_stats = m.opponent_stats(matches)

    args = {
        "matches": matches[offset:offset + config.match_limit],
        "modes": ["All", "Ranked"] + list(reversed(config.modes)),
        "opponents": ["All"] + config.heroes,
        "from_date": from_date,
        "to_date": to_date,
        "mode": mode,
        "deck": deck,
        "opponent": opponent,
        "opponent_stats": opponent_stats,
        "opponent_ratios": opponent_ratios(opponent_stats),
        "notes": notes,
        "outcome": outcome,
        "total": total,
        "total_ratio": total_ratio,
        "matches_found": matches_found,
        "offset": offset,
        "prev_url": prev_url,
        "next_url": next_url,
        "limit": config.match_limit,
        "current_page": int(offset / config.match_limit) + 1,
        "total_pages": int(matches_found / config.match_limit) + 1,
        "prev_pages_left": offset > 0,
        "next_pages_left": offset + config.match_limit < matches_found,
        "winrate": stats["winrate"]
    }

    return render_template("matches.html", **args)

@app.route("/cards")
def cards():
    c = Cards(db)
    search = {}

    name = request.args.get("name", "")
    text = request.args.get("text", "")
    mana = request.args.get("mana", "")
    attack = request.args.get("attack", "")
    health = request.args.get("health", "")
    notes = request.args.get("notes", "")
    offset = request.args.get("offset", "")
    missing = request.args.get("missing", "")

    hero = request.args.getlist("hero")
    rarity = request.args.getlist("rarity")
    card_set = request.args.getlist("set")
    card_type = request.args.getlist("type")
    mechanics = request.args.getlist("mechanics")

    if name != "":
        search["name"] = name

    if text != "":
        search["text"] = text

    if len(hero) > 0 and "All" not in hero:
        search["hero"] = hero

    if mana != "":
        search["cost"] = mana

    if attack != "":
        search["attack"] = attack

    if health != "":
        search["health"] = health

    if len(rarity) > 0 and "All" not in rarity:
        search["rarity"] = rarity

    if len(card_set) > 0 and "All" not in card_set:
        search["card_set"] = card_set

    if len(card_type) > 0 and "All" not in card_type:
        search["card_type"] = card_type

    if len(mechanics) > 0 and "All" not in mechanics:
        search["mechanics"] = mechanics

    if notes != "":
        search["notes"] = notes

    missing_cards = c.missing()

    if missing != "":
        cards = missing_cards[0]
    else:
        cards = c.search(**search)
    total = len(cards)

    if offset != "" and is_int(offset):
        offset = int(offset)
    else:
        offset = 0

    dust_needed = c.dust_needed()
    if len(dust_needed.keys()) > 0:
        packs = sorted(list(dust_needed.items()), key=lambda x: x[0])
        buy_pack = sorted(packs, key=lambda x: x[1], reverse=True)[0][0]
    else:
        packs = []
        buy_pack = None

    prev_offset = offset - config.card_limit
    if prev_offset < 0:
        prev_offset = 0
    next_offset = offset + config.card_limit
    if next_offset > total:
        next_offset = total - config.card_limit

    query = request.query_string.decode()
    prev_url = update_query_offset(query, prev_offset)
    next_url = update_query_offset(query, next_offset)

    args = {
        "cards": [format_card(x) for x in
                  cards[offset:offset + config.card_limit]],
        "heroes": ["All", "Neutral"] + config.heroes,
        "rarities": ["All"] + [x.title() for x in c.rarities()],
        "card_sets": ["All"] + [x for x in c.sets()],
        "card_types": ["All"] + [x.title() for x in c.types()],
        "mechanics": ["All"] + [x.title() for x in c.mechanics()],
        "hero": hero,
        "name": name,
        "text": text,
        "mana": mana,
        "attack": attack,
        "health": health,
        "rarity": rarity,
        "card_set": card_set,
        "card_type": card_type,
        "mechanic": mechanics,
        "notes": notes,
        "offset": offset,
        "prev_url": prev_url,
        "next_url": next_url,
        "limit": config.card_limit,
        "current_page": int(offset / config.card_limit) + 1,
        "total_pages": int(total / config.card_limit) + 1,
        "prev_pages_left": offset > 0,
        "next_pages_left": offset + config.card_limit < total,
        "all_cards": c.total(),
        "total_ratio": winrate(c.total(), total),
        "card_image_url": config.card_image_url,
        "dust_needed": packs,
        "buy_pack": buy_pack,
        "total_missing": missing_cards[1],
        "total": total
    }

    return render_template("cards.html", **args)

@app.route("/add_card/<card_id>")
@requires_auth
def add_card(card_id):
    c = Cards(db)
    return str(c.add_owned(card_id))

@app.route("/remove_card/<card_id>")
@requires_auth
def remove_card(card_id):
    c = Cards(db)
    return str(c.remove_owned(card_id))

@app.route("/set_notes/<card_id>/<notes>")
@requires_auth
def set_notes(card_id, notes):
    c = Cards(db)
    return str(c.set_notes(card_id, notes))

@app.route("/matches.json")
@requires_auth
def export_matches():
    m = Matches(db)
    matches = m.backup()
    return Response(response=dumps(matches),
                    status=200,
                    mimetype="application/json")

@app.route("/collection.json")
@requires_auth
def export_collection():
    c = Cards(db)
    collection = c.backup_collection()
    return Response(response=dumps(collection),
                    status=200,
                    mimetype="application/json")

@app.route("/logout")
@requires_auth
def logout():
    session.pop("username", None)
    return render_template("logout.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    login_failed = False
    if not "username" in session and request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        authed = (username == credentials["username"] and
                  password == credentials["password"])
        if authed:
            session.permanent = True
            session["username"] = username
            return render_template("login.html")
        else:
            login_failed = True

    return render_template("login.html", login_failed=login_failed)
