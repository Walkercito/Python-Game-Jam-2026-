LEVELS: dict[str, dict] = {
    "tutorial_001": {
        "map": "assets/tiled/tutorial_001.tmx",
        "zone_subtitle": "Zone One",
        "zone_title": "Tutorial Valley",
        "signs": {
            0: "Stand on both plates to open the portal!",
        },
        "next_level": "level_001",
        "zoom": None,
        "tutorial": [
            {"keys": ["A", "D"], "text": "Move", "action": "move"},
            {"keys": ["W"], "text": "Jump", "action": "jump"},
            {"keys": ["W", "W"], "text": "Double jump at the peak!", "action": "double_jump"},
            {"keys": ["S"], "text": "Fast fall", "action": "fast_fall"},
        ],
    },
    "level_001": {
        "map": "assets/tiled/level_001.tmx",
        "zone_subtitle": "Zone Two",
        "zone_title": "The Farlands",
        "signs": {
            0: "Careful with the lava!",
            1: "Climb the stairs together",
            2: "These platforms won't hold long...",
            3: "Stand on both plates!",
        },
        "next_level": None,
        "zoom": 5.0,  # closer zoom — players feel bigger
    },
}
