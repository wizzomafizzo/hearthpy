# hearthpy global config

db_filename = "hearthpy.db"
auth_filename = "hearthpy.auth"
port = 5000
match_limit = 20
front_match_limit = 20
card_limit = 24
winrate_tiers = [50, 55]  # %
min_games_deck = 20

deck_template = "^(S|W)(Dd|Hr|Me|Pn|Pt|Re|Sn|Wk|Wr) .+ \d+\.\d+$"
card_image_url = "http://media.services.zam.com/v1/media/byName/hs/cards/enus/{}.png"
cards_json_url = "https://api.hearthstonejson.com/v1/20457/enUS/cards.collectible.json"
cards_json_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36"

card_packs = ["EXPERT1", "GVG", "ICECROWN", "TGT", "OG", "GANGS", "UNGORO"]
standard_sets = ["CORE", "EXPERT1", "ICECROWN", "KARA", "GANGS", "OG", "UNGORO"]
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
