#!/usr/bin/env python3
"""
Keystone Facebook Auto-Poster v2.0
Fixes: Uses Hugging Face Inference API (free tier) for image generation
Replaces broken Picsum random images with branded, relevant AI images.

Usage: python fb_poster.py --post-type korea_tip --caption-file caption.txt
"""

import requests
import os
import json
import random
from PIL import Image, ImageDraw, ImageFont
import io
import base64

# CONFIG
HF_API_TOKEN = os.getenv("HF_API_TOKEN", "hf_YOUR_TOKEN_HERE")  # Get from huggingface.co/settings/tokens
HF_MODEL = "stabilityai/stable-diffusion-xl-base-1.0"
FB_PAGE_TOKEN = os.getenv("FB_PAGE_TOKEN", "YOUR_FB_PAGE_TOKEN")
PAGE_ID = "1003817206350395"
LOGO_PATH = "logo.png"  # Upload your Keystone logo

# Prompt templates for different post types
PROMPT_TEMPLATES = {
    "korea_tip": [
        "A young Bangladeshi student walking on a modern university campus in South Korea, cherry blossom trees, bright sunny day, photorealistic, 4k",
        "A Bangladeshi student studying in a Korean university library, books and laptop, warm lighting, professional photography",
        "South Korean university campus with traditional Korean architecture mixed with modern buildings, students walking, vibrant colors"
    ],
    "success_story": [
        "A young Bangladeshi student holding a Korean university acceptance letter, smiling, professional portrait, bright background",
        "A graduation ceremony at a Korean university, Bangladeshi student in cap and gown, proud moment, photorealistic"
    ],
    "document_guide": [
        "A clean desk with organized documents, passport, bank statement, academic certificates, professional flat lay photography, warm lighting",
        "A person carefully reviewing documents with a pen, checklist on desk, professional office setting, sharp focus"
    ],
    "ielts": [
        "A student taking an IELTS exam, focused concentration, modern test center, professional photography",
        "Books and study materials for English language test, IELTS preparation, organized desk, motivational"
    ],
    "general": [
        "International students from diverse backgrounds studying together in a modern classroom, South Korea, bright and welcoming",
        "A world map with South Korea highlighted, travel and education concept, modern graphic design, clean aesthetic"
    ]
}

BANGLA_CAPTION_TEMPLATES = {
    "korea_tip": [
        "🇰🇷 কোরিয়াতে পড়াশোনা করতে চান? আমাদের ফ্রি কাউন্সেলিং এ আসুন!\n\n📍 নারসিংদি বাজার, কিস্টোন এডুকেশন\n📞 01328-224600\n\n#StudyInKorea #KoreaEducation #Narsingdi #KeystoneEducation",
        "🎓 কোরিয়ার বিশ্ববিদ্যালয়ে ভর্তি হতে চান?\n\n✅ IELTS ছাড়াও সুযোগ\n✅ ৫ বছর স্টাডি গ্যাপ গ্রহণযোগ্য\n✅ পার্ট-টাইম জবের সুযোগ\n\nফ্রি কাউন্সেলিং এর জন্য আজই আসুন!\n\n📞 01328-224600"
    ],
    "success_story": [
        "🎉 আরেকটি সাকসেস! [STUDENT_NAME] কোরিয়ার [UNIVERSITY_NAME] তে ভর্তি হয়েছে!\n\nআপনিও কি কোরিয়াতে পড়তে চান?\n\n📞 কল করুন: 01328-224600\n📍 অফিস: নারসিংদি বাজার",
        "💪 স্বপ্ন সত্যি হতে পারে!\n\nআমাদের আরেক ছাত্র কোরিয়ায় ভিসা পেয়েছে। আপনিও পারবেন!\n\nফ্রি কাউন্সেলিং — আজই আসুন।"
    ],
    "document_guide": [
        "📋 কোরিয়ার ভিসার জন্য কী কী ডকুমেন্ট লাগে?\n\n✅ পাসপোর্ট\n✅ HSC সার্টিফিকেট\n✅ ব্যাংক স্টেটমেন্ট (USD 10,000-20,000)\n✅ পুলিশ ক্লিয়ারেন্স\n✅ TB টেস্ট\n\nবিস্তারিত জানতে আসুন অফিসে!\n\n📞 01328-224600",
        "⚠️ সাধারণ ভুল যেগুলো ভিসা রিজেক্ট করায়!\n\n❌ ব্যাংক স্টেটমেন্টে টাকা কম\n❌ ডকুমেন্টে স্বাক্ষর নেই\n❌ ছবির সাইজ ভুল\n\nআমরা আপনার সব ডকুমেন্ট চেক করে দিই।\n\n📞 01328-224600"
    ],
    "ielts": [
        "📝 IELTS ছাড়াই কোরিয়ায় পড়ার সুযোগ!\n\nEAP প্রোগ্রামে ভর্তি হলে IELTS লাগে না।\n\nতবে IELTS থাকলে স্কলারশিপ পাবেন!\n\n📞 জানতে কল করুন: 01328-224600",
        "🎯 IELTS স্কোর = স্কলারশিপ!\n\nIELTS 6.0 = ৩০-৫০% স্কলারশিপ\nIELTS 6.5 = ৫০-১০০% স্কলারশিপ\n\nIELTS কোচিং কোথায় করবেন? আমরা সেরা কোচিং সেন্টার রেকমেন্ড করি!\n\n📞 01328-224600"
    ],
    "general": [
        "🌍 বিশ্বমানের শিক্ষা, কাছের দামে!\n\nকোরিয়ায় পড়াশোনা:\n💰 সেমিস্টার ফি: USD 2,000-5,000\n💼 পার্ট-টাইম: ২০ ঘণ্টা/সপ্তাহ\n🏠 হোস্টেল: সাশ্রয়ী\n\nফ্রি কাউন্সেলিং এ আসুন!\n\n📞 01328-224600\n📍 নারসিংদি বাজার",
        "🤔 কোন দেশে পড়বো?\n\n✅ কোরিয়া — কম খরচ, ভালো জব\n✅ মালয়েশিয়া — ইংরেজি মাধ্যম\n✅ কানাডা — পিআর সুযোগ\n\nআপনার প্রোফাইল অনুযায়ী সেরা দেশ বলে দিই!\n\n📞 ফ্রি কাউন্সেলিং: 01328-224600"
    ]
}


def generate_image_hf(prompt, api_token):
    """Generate image using Hugging Face Inference API (free tier)."""
    if api_token == "hf_YOUR_TOKEN_HERE":
        print("⚠️  No HF token. Using fallback: branded template image.")
        return create_fallback_image()

    API_URL = f"https://api-inference.huggingface.co/models/{HF_MODEL}"
    headers = {"Authorization": f"Bearer {api_token}"}
    payload = {"inputs": prompt}

    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=60)
        if response.status_code == 200:
            image_bytes = response.content
            return Image.open(io.BytesIO(image_bytes))
        else:
            print(f"HF API error: {response.status_code} — {response.text}")
            return create_fallback_image()
    except Exception as e:
        print(f"Error generating image: {e}")
        return create_fallback_image()


def create_fallback_image():
    """Create a branded fallback image if AI generation fails."""
    img = Image.new("RGB", (1200, 630), color="#1a1a2e")
    draw = ImageDraw.Draw(img)

    # Try to load a font, fallback to default
    try:
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 36)
    except:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # Draw text
    draw.text((600, 200), "Keystone Education", fill="#ffffff", font=font_large, anchor="mm")
    draw.text((600, 300), "Study in South Korea", fill="#60a5fa", font=font_small, anchor="mm")
    draw.text((600, 400), "📞 01328-224600", fill="#ffffff", font=font_small, anchor="mm")

    return img


def overlay_logo(image, logo_path):
    """Overlay Keystone logo on bottom right."""
    if not os.path.exists(logo_path):
        return image

    try:
        logo = Image.open(logo_path).convert("RGBA")
        # Resize logo to 150px width
        ratio = 150 / logo.width
        new_size = (150, int(logo.height * ratio))
        logo = logo.resize(new_size, Image.LANCZOS)

        # Paste on bottom right
        position = (image.width - logo.width - 20, image.height - logo.height - 20)
        image.paste(logo, position, logo)
    except Exception as e:
        print(f"Logo overlay error: {e}")

    return image


def post_to_facebook(image, caption, page_token, page_id):
    """Post image + caption to Facebook page."""
    if page_token == "YOUR_FB_PAGE_TOKEN":
        print("⚠️  No FB token. Saving image locally instead.")
        image.save("fb_post.png")
        print(f"   Image saved: fb_post.png")
        print(f"   Caption: {caption[:100]}...")
        return None

    # Save image temporarily
    img_buffer = io.BytesIO()
    image.save(img_buffer, format="PNG")
    img_buffer.seek(0)

    url = f"https://graph.facebook.com/v18.0/{page_id}/photos"
    files = {"file": ("post.png", img_buffer, "image/png")}
    data = {
        "message": caption,
        "access_token": page_token
    }

    try:
        response = requests.post(url, files=files, data=data, timeout=30)
        result = response.json()
        if "id" in result:
            print(f"✅ Posted successfully! Post ID: {result['id']}")
            return result
        else:
            print(f"❌ Post failed: {result}")
            return None
    except Exception as e:
        print(f"Error posting: {e}")
        return None


def create_post(post_type="general", custom_caption=None, custom_prompt=None):
    """Create and post a single piece of content."""

    # Select prompt
    if custom_prompt:
        prompt = custom_prompt
    else:
        prompt = random.choice(PROMPT_TEMPLATES.get(post_type, PROMPT_TEMPLATES["general"]))

    # Select caption
    if custom_caption:
        caption = custom_caption
    else:
        caption = random.choice(BANGLA_CAPTION_TEMPLATES.get(post_type, BANGLA_CAPTION_TEMPLATES["general"]))

    print(f"🎨 Generating image for: {post_type}")
    print(f"   Prompt: {prompt[:80]}...")

    # Generate image
    image = generate_image_hf(prompt, HF_API_TOKEN)

    # Overlay logo
    image = overlay_logo(image, LOGO_PATH)

    # Post
    print(f"📝 Posting to Facebook...")
    result = post_to_facebook(image, caption, FB_PAGE_TOKEN, PAGE_ID)

    return result


def batch_schedule():
    """
    Recommended posting schedule for Marina:

    Monday:    korea_tip
    Tuesday:   document_guide
    Wednesday: ielts
    Thursday:  success_story (if available) or korea_tip
    Friday:    general
    Saturday:  ielts or korea_tip
    Sunday:    OFF or community engagement

    Run this script daily via cron or manually.
    """
    schedule = {
        0: "korea_tip",      # Monday
        1: "document_guide", # Tuesday
        2: "ielts",          # Wednesday
        3: "korea_tip",      # Thursday
        4: "general",        # Friday
        5: "ielts",          # Saturday
        6: None              # Sunday
    }

    import datetime
    today = datetime.datetime.now().weekday()
    post_type = schedule.get(today)

    if post_type:
        print(f"📅 Today is {['Mon','Tue','Wed','Thu','Fri','Sat','Sun'][today]}")
        print(f"   Scheduled post type: {post_type}")
        create_post(post_type=post_type)
    else:
        print("📅 Sunday — no scheduled post. Engage with comments instead.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--post-type", default="general", choices=list(PROMPT_TEMPLATES.keys()))
    parser.add_argument("--caption", help="Custom Bangla caption")
    parser.add_argument("--prompt", help="Custom image prompt")
    parser.add_argument("--schedule", action="store_true", help="Use daily schedule")
    parser.add_argument("--batch", action="store_true", help="Generate 7 posts for the week")

    args = parser.parse_args()

    if args.schedule:
        batch_schedule()
    elif args.batch:
        for i, (day, ptype) in enumerate([
            ("Mon", "korea_tip"), ("Tue", "document_guide"), ("Wed", "ielts"),
            ("Thu", "success_story"), ("Fri", "general"), ("Sat", "ielts")
        ]):
            print(f"\n{'='*50}")
            print(f"📅 {day}")
            create_post(post_type=ptype)
    else:
        create_post(post_type=args.post_type, custom_caption=args.caption, custom_prompt=args.prompt)
