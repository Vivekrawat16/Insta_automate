#!/usr/bin/env python3
"""
Cluster Generator for @vformemes
Takes the winning topic from performance auditor and creates 3 high-impact
spin-off meme reel specifications clustered around that winning theme.
"""

import os
import random
from pathlib import Path
from typing import List, Dict

BASE_DIR = Path(__file__).resolve().parent
CLIPS_DIR = BASE_DIR / "assets" / "clips"

# Topic-based cluster templates repository
CLUSTER_LIBRARY = {
    "chaar_log_relatives": [
        {
            "slug": "fufaji_wfh_interrogation",
            "raw_video": "paresh_raw.mp4",
            "aspect": "16:9",
            "duration": 6.8,
            "ss_offset": 0,
            "lines": [
                "Shaadi me door ke fufaji puchte hain:",
                "'Beta 2 saal se ghar baith ke laptop pe",
                "kya karte ho, sachme naukri hai ya",
                "papa ke paise uda rahe ho?'"
            ],
            "caption": "Fufaji ki interrogation CBI se zyada dangerous hai 💀😭 Har shaadi me ek interview round compulsory hai.\n\nTag that relative who questions your entire existence! 😂👇\n\n#chaarlog #relatives #indianwedding #desimemes #relatable #familydrama #vformemes"
        },
        {
            "slug": "aunty_swiggy_delivery_stare",
            "raw_video": "baburao_raw.mp4",
            "aspect": "16:9",
            "duration": 7.4,
            "ss_offset": 0,
            "lines": [
                "Mohalle ki aunty ne raat 10 baje",
                "Zomato delivery boy ko aate dekh liya...",
                "agla phone sidha mummy ko:",
                "'Bhabhi ji, ghar me khana nahi ban raha kya?'"
            ],
            "caption": "Aunty ka CCTV surveillance network NASA se zyada active hai 💀😭 Ek burger order kiya tha pure mohalle me khabar ho gayi.\n\nTag that neighbor aunty! 😂👇\n\n#desiaunty #zomato #mohalla #indianhousehold #desicomedy #vformemes #laughter"
        },
        {
            "slug": "sharmaji_beta_ctc_dinner",
            "raw_video": "cillian_raw.mp4",
            "aspect": "16:9",
            "duration": 6.5,
            "ss_offset": 0,
            "lines": [
                "Dinner table par papa ne Sharma ji ke",
                "bete ka 45 LPA remote package sun liya...",
                "aur ab bina kuch bole bas",
                "meri thali ki roti ko ghoor rahe hain"
            ],
            "caption": "Jab silence me bhi taane sunai dene lagein 💀😭 Comparison syndrome at peak level.\n\nDrop an 'F' in comments if your parents compare you to Sharma ji ka beta! 😭\n\n#sharmajikabeta #indianparents #ctccomparison #corporatehumor #vformemes"
        },
        {
            "slug": "biodata_ctc_roundoff",
            "raw_video": "rajpal_raw.mp4",
            "aspect": "16:9",
            "duration": 6.0,
            "ss_offset": 0,
            "lines": [
                "Shaadi ke biodata me CTC 18 Lakh likhi thi...",
                "ladki ke mama ne Form 16 aur",
                "in-hand salary slip maang li...",
                "meri halat kharab ho gayi"
            ],
            "caption": "CTC vs In-hand ka sach rishte tudwa sakta hai 💀😭 Stocks aur PF count karke 18L banaya tha bhaiya.\n\nTag a friend looking for rishtas! 😂👇\n\n#matrimony #ctcvsinhand #arrangedmarriage #desimemes #vformemes"
        }
    ],
    "landlord_pg": [
        {
            "slug": "landlord_wall_aura_deduction",
            "raw_video": "rajpal_raw.mp4",
            "aspect": "16:9",
            "duration": 6.0,
            "ss_offset": 0,
            "lines": [
                "Flat chhodte waqt landlord ne",
                "15,000 security deposit me se",
                "'Diwaar ki positive aura kam hone ka'",
                "12,000 kaat liya..."
            ],
            "caption": "Bangalore/Delhi landlords deduct money for breathing inside the flat 💀😭 Deposit wapsi is a myth.\n\nTag your roommates who lost security deposit! 😂👇\n\n#landlordproblems #pglife #bangalorelandlords #securitydeposit #desicomedy #vformemes"
        },
        {
            "slug": "landlord_geyser_meter_warning",
            "raw_video": "baburao_raw.mp4",
            "aspect": "16:9",
            "duration": 7.4,
            "ss_offset": 0,
            "lines": [
                "Month ka 16,000 rent dene ke baad",
                "landlord notice board par likh gaya:",
                "'Geyser 10 minute se zyada chala",
                "toh unit rate double lagega beta'"
            ],
            "caption": "Sardiyon me geyser chalane ki permission lene ke liye application likhni padegi 💀😭 PG landlord supremacy.\n\nTag your landlord! 😂👇\n\n#pglife #landlorddrama #winterstruggles #indianmemes #vformemes"
        },
        {
            "slug": "bachelor_flat_interview_rounds",
            "raw_video": "nana_raw.mp4",
            "aspect": "16:9",
            "duration": 6.8,
            "ss_offset": 0,
            "lines": [
                "1BHK rent pe lene gaya tha...",
                "society uncle ne 10th marksheet,",
                "LinkedIn profile aur 3 reference maang liye...",
                "Google interview se bhi zyada tough hai"
            ],
            "caption": "Bachelor hona is a crime in Indian societies 💀😭 IIT degree ke baad bhi bachelor flat rejection milta hai.\n\nTag all bachelors surviving out there! 😂👇\n\n#bachelorlife #societyrules #indianrentals #delhincr #bangalore #vformemes"
        }
    ],
    "corporate_majdoori": [
        {
            "slug": "appraisal_invest_dialogue",
            "raw_video": "akshay_raw.mp4",
            "aspect": "16:9",
            "duration": 6.5,
            "ss_offset": 0,
            "lines": [
                "Appraisal me hike mili 2.1%...",
                "par manager meeting me aisi acting kar raha hai",
                "jaise usne mujhe apni kidney",
                "aur property daan me de di ho"
            ],
            "caption": "2.1% hike dekar bolte hain 'Company has huge plans for your career' 💀😭 Corporate comedy at peak.\n\nTag your manager if you're feeling brave! 😂👇\n\n#corporatehumor #appraisalseason #hike2percent #corporatemajdoor #vformemes"
        },
        {
            "slug": "friday_five_fifty_nine_ping",
            "raw_video": "cillian_raw.mp4",
            "aspect": "16:9",
            "duration": 6.5,
            "ss_offset": 0,
            "lines": [
                "Friday shaam 5:59 PM par laptop",
                "shut down karne hi wala tha...",
                "aur manager ka Teams notification pop hua:",
                "'Quick sync beta, 5 mins only'"
            ],
            "caption": "Wo 5 min ka quick sync 2 ghante aur Monday ka dukh ban jata hai 💀😭 Weekend plan cancelled.\n\nTag your colleague who relates! 😭👇\n\n#corporatelife #teamsnotification #fridayquicksync #desimemes #vformemes"
        }
    ]
}

def resolve_video_path(filename: str) -> str:
    """Finds clip in assets/clips or fallback locations."""
    target = CLIPS_DIR / filename
    if target.exists():
        return str(target)
    # Fallback to local nifi build if running locally
    local_fallback = Path("/home/vivek/nifi/meme_build") / filename
    if local_fallback.exists():
        return str(local_fallback)
    return str(target)

def generate_cluster_batch(winning_topic: str = "chaar_log_relatives", count: int = 3) -> List[Dict]:
    """Generates 3-4 spin-off meme specifications for the winning topic."""
    pool = CLUSTER_LIBRARY.get(winning_topic) or CLUSTER_LIBRARY["chaar_log_relatives"]
    selected = random.sample(pool, min(count, len(pool)))
    # Resolve video paths
    for item in selected:
        item["resolved_video"] = resolve_video_path(item["raw_video"])
    return selected

if __name__ == "__main__":
    specs = generate_cluster_batch("chaar_log_relatives", count=3)
    for s in specs:
        print(f"- {s['slug']} ({s['resolved_video']}): {s['lines'][0]}...")
