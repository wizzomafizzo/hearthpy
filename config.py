# hearthpy global config

db_filename = "hearthpy.db"
auth_filename = "hearthpy.auth"
port = 5000
match_limit = 20
front_match_limit = 21
card_limit = 24
winrate_tiers = [50, 55]  # %
min_games_deck = 20

deck_template = "^(S|W)(Dd|Hr|Me|Pn|Pt|Re|Sn|Wk|Wr) .+ \d+\.\d+$"
card_image_url = "http://wow.zamimg.com/images/hearthstone/cards/enus/original/{}.png"
# cards_json_url = "https://api.hearthstonejson.com/v1/latest/enUS/cards.collectible.json"
cards_json_url = "https://api.hearthstonejson.com/v1/17720/enUS/cards.collectible.json"

card_packs = ["EXPERT1", "GVG", "TGT", "OG", "GANGS"]
standard_sets = ["BRM", "CORE", "EXPERT1", "KARA", "GANGS", "LOE", "OG", "TGT"]
craft_cost = {
    "COMMON": 40,
    "RARE": 100,
    "EPIC": 400,
    "LEGENDARY": 1600
}

heroes = [
    "Druid",
    "Hunter",
    "Mage",
    "Paladin",
    "Priest",
    "Rogue",
    "Shaman",
    "Warlock",
    "Warrior"
]

heroes_abbrv = {
    "Dd": "Druid",
    "Hr": "Hunter",
    "Me": "Mage",
    "Pn": "Paladin",
    "Pt": "Priest",
    "Re": "Rogue",
    "Sn": "Shaman",
    "Wk": "Warlock",
    "Wr": "Warrior"
}

modes = [
    "Legend",
    "Rank 1",
    "Rank 2",
    "Rank 3",
    "Rank 4",
    "Rank 5",
    "Rank 6",
    "Rank 7",
    "Rank 8",
    "Rank 9",
    "Rank 10",
    "Rank 11",
    "Rank 12",
    "Rank 13",
    "Rank 14",
    "Rank 15",
    "Rank 16",
    "Rank 17",
    "Rank 18",
    "Rank 19",
    "Rank 20",
    "Rank 21",
    "Rank 22",
    "Rank 23",
    "Rank 24",
    "Rank 25",
    "Casual"
]
