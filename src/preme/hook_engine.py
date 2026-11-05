#!/usr/bin/env python3
"""
Preme Viral Hook & Caption Engine
Generates irresistible, click-worthy 2-line hooks and high-reach captions
tailored for US/UK/CA short-form video audiences (Reels/TikTok).
"""

import re
from typing import Dict

COMMON_HOOK_PATTERNS = [
    # Donations / Blessings
    (
        r"(bless|cash|1000|dollar|money|family)",
        "PREME BLESSES A RANDOM FAMILY",
        "WITH $1,000 CASH ON STREAM 😭💵",
        "Bro really made their entire month... 🥹 Moments like this are why Preme is a W streamer! ❤️\n\nDrop a 'W' in the comments if you love wholesome streams! 🙌\n\n#preme #streamer #kickstreamer #wholesome #gooddeed #viralreels #kicklive"
    ),
    # Car gifts
    (
        r"(car|gift mom|daughter)",
        "PREME SURPRISES A MOM & DAUGHTER",
        "WITH A BRAND NEW CAR 😭🚗",
        "Her reaction had everyone in chat tearing up... 🥹 Preme really changed their lives forever!\n\nTag someone who needs to see this today! ❤️\n\n#preme #streamer #wholesome #carreveal #gooddeed #kick #twitch #viralreels"
    ),
    # Accents / funny voice
    (
        r"(accent|voice|accent|british|toronto)",
        "PREME TRIED TO SWITCH HIS ACCENT",
        "AND IT WENT HORRIBLY WRONG 💀😭",
        "The chat was ruthless for this one 💀 Bro couldn't keep a straight face for more than 5 seconds 😂\n\nTag a friend who tries too hard to sound different! 😭\n\n#preme #streamer #roast #funny #comedy #kickclips #twitchclips #streamerfails"
    ),
    # Outfits / Roasts
    (
        r"(fit|roast|superhero|clothe|jacket|outfit)",
        "HE WALKED IN WEARING THIS FIT",
        "AND THE ENTIRE CHAT ROASTED HIM 💀",
        "The disrespect in chat was completely unprovoked 💀😭 Would you ever rock this fit outside?\n\nTell us your honest 1-10 rating in the comments! 👇😂\n\n#preme #streamer #roast #fashionfails #streamermoments #kick #twitch"
    ),
    # Chat burst / Drama / Freakouts
    (
        r"(burst|what|insane|wild|omg|crazy|shout)",
        "SOMETHING WILD JUST HAPPENED",
        "AND PREME COULD NOT BELIEVE IT 🤯",
        "Chat was moving at 100 messages a second when this happened 💀 Drop your reaction in the comments! 👇\n\n#preme #kick #streamer #viralmoments #clipping #reaction"
    ),
    # Mind your business / confrontation
    (
        r"(business|mind your|street|stranger|confront)",
        "WHEN SOMEONE TELLS THE STREAMER",
        "TO MIND HIS OWN BUSINESS 💀😭",
        "Bro really thought he was about to get away with that 💀 The tension was unreal!\n\nTag that friend who can never mind their own business! 😂\n\n#preme #irlstream #streetinterviews #kickstreamer #viral"
    )
]

def generate_hook_and_caption(clip_title: str) -> Dict[str, str]:
    """
    Analyzes clip title / metadata and generates:
    - hook_line1 (Context setup)
    - hook_line2 (Punchline / Payoff)
    - caption (Full caption with hashtags)
    """
    title_lower = clip_title.lower()

    # Match predefined high-converting patterns
    for pattern, h1, h2, cap in COMMON_HOOK_PATTERNS:
        if re.search(pattern, title_lower):
            return {
                "hook_line1": h1,
                "hook_line2": h2,
                "caption": cap
            }

    # Fallback dynamic generator
    clean_title = re.sub(r"[#@!🦉👽🛸]", "", clip_title).strip()
    words = clean_title.split()

    if len(words) <= 4:
        h1 = "WHEN PREME REALIZED"
        h2 = clean_title.upper() + " 💀😭"
    else:
        mid = len(words) // 2
        h1 = " ".join(words[:mid]).upper()
        h2 = " ".join(words[mid:]).upper() + " 💀"

    fallback_caption = (
        f"This moment from Preme's stream was pure comedy 💀😭\n\n"
        f"Tag a friend who watches Preme! 👇\n\n"
        f"#preme #kick #streamer #irlstream #twitch #clipping #fyp #explorepage"
    )

    return {
        "hook_line1": h1,
        "hook_line2": h2,
        "caption": fallback_caption
    }

if __name__ == "__main__":
    test_titles = [
        "LOL PREME ACCENT",
        "gift mom car",
        "blessing a family with $1000"
    ]
    for t in test_titles:
        res = generate_hook_and_caption(t)
        print(f"Title: {t}")
        print(f"  Line 1: {res['hook_line1']}")
        print(f"  Line 2: {res['hook_line2']}")
