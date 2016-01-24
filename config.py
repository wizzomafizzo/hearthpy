# hearthpy global config

db_filename = "hearthpy.db"
auth_filename = "hearthpy.auth"
port = 5000
url_prefix = "/hs"
match_limit = 16
front_match_limit = 17
card_limit = 23
winrate_tiers = [50, 60] # %
deck_template = "^(Dd|Hr|Me|Pn|Pt|Re|Sn|Wk|Wr) .+ \d+\.\d+$"
card_image_url = "http://wow.zamimg.com/images/hearthstone/cards/enus/original/{}.png"
cards_json_url = "https://api.hearthstonejson.com/v1/latest/enUS/cards.collectible.json"
card_packs = ["EXPERT1", "GVG", "TGT"]
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
