"""
Ọ̀NÀ Telegram bot (@OnaYorubaBot) — same Supabase database as the site, so
every domain (words, proverbs, Ifá, quiz, search) has feature parity here.
Uses the service_role key server-side only; never exposed to users.
"""
import logging
import os
import random
from datetime import date
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("ona-bot")

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_KEY = os.environ["SUPABASE_SERVICE_KEY"]

sb = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

BADGE_LABELS = {
    "verified_multi_source": "✅ Verified (multi-source)",
    "verified_single_source": "✅ Sourced",
    "fieldwork_verified": "✅ Fieldwork verified",
    "fieldwork_partial": "🟡 Fieldwork (partial)",
    "ai_generated_unverified": "🟠 AI research — unverified",
    "web_sourced_pending_verification": "🟠 Community-sourced — unverified",
    "disputed": "🔴 Disputed sources",
    "unverified": "⚪ Unverified",
}

HELP_TEXT = (
    "*Ọ̀NÀ — Yoruba words, proverbs, Ifá/Odù, and culture*\n\n"
    "/word — a random Yoruba word\n"
    "/proverb — a random òwe (proverb)\n"
    "/ifa — a random Ifá/Òrìṣà entry\n"
    "/wotd — word of the day\n"
    "/potd — proverb of the day\n"
    "/quiz — play a round of Nje O Mọ\n"
    "/search <term> — full-text search, or just send any message\n"
    "/favorites — your saved entries\n"
    "/about — contact &amp; how entries are verified\n\n"
    "Same archive as onayoruba site (link in /about) — anything added there shows up here too."
)


def format_entry(e: dict) -> str:
    badge = BADGE_LABELS.get(e.get("verify_status"), e.get("verify_status", ""))
    lines = []
    if e.get("yoruba"):
        lines.append(f"*{e['yoruba']}*")
    if e.get("english"):
        lines.append(f"_{e['english']}_")
    if e.get("drop_english"):
        lines.append("")
        lines.append(e["drop_english"])
    lines.append("")
    meta = badge
    if e.get("domain"):
        meta += f" · {e['domain']}"
    if e.get("category"):
        meta += f" · {e['category']}"
    lines.append(meta)
    if e.get("source_citation"):
        lines.append(f"Source: {e['source_citation']}")
    return "\n".join(lines)


def entry_keyboard(e: dict, reveal=False) -> InlineKeyboardMarkup:
    buttons = []
    if reveal:
        buttons.append(InlineKeyboardButton("Fi ìdáhùn hàn — Reveal answer", callback_data=f"reveal:{e['id']}"))
    buttons.append(InlineKeyboardButton("⭐ Favorite", callback_data=f"fav:{e['id']}"))
    return InlineKeyboardMarkup([buttons])


def upsert_user(update: Update):
    u = update.effective_user
    sb.table("users").upsert(
        {
            "telegram_id": u.id,
            "username": u.username,
            "first_name": u.first_name,
            "last_active_at": "now()",
        },
        on_conflict="telegram_id",
    ).execute()


def random_entry(domain: str | list[str]):
    domains = domain if isinstance(domain, list) else [domain]
    res = sb.table("entries").select("*").in_("domain", domains).execute()
    rows = res.data
    if not rows:
        return None
    return random.choice(rows)


def entry_of_the_day(domain: str):
    res = sb.table("entries").select("*").eq("domain", domain).order("id").execute()
    rows = res.data
    if not rows:
        return None
    idx = date.today().timetuple().tm_yday % len(rows)
    return rows[idx]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    upsert_user(update)
    await update.message.reply_text(
        f"Ẹ nlẹ́, {update.effective_user.first_name}! Ọ̀NÀ ń kí ẹ.\n\n" + HELP_TEXT,
        parse_mode=ParseMode.MARKDOWN,
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(HELP_TEXT, parse_mode=ParseMode.MARKDOWN)


async def word_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    e = random_entry("vocab")
    if not e:
        await update.message.reply_text("No words available right now.")
        return
    await update.message.reply_text(format_entry(e), parse_mode=ParseMode.MARKDOWN, reply_markup=entry_keyboard(e))


async def proverb_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    e = random_entry("owe")
    if not e:
        await update.message.reply_text("No proverbs available right now.")
        return
    await update.message.reply_text(format_entry(e), parse_mode=ParseMode.MARKDOWN, reply_markup=entry_keyboard(e))


async def ifa_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    e = random_entry(["ifa", "orisa"])
    if not e:
        await update.message.reply_text("No Ifá/Òrìṣà entries available right now.")
        return
    await update.message.reply_text(format_entry(e), parse_mode=ParseMode.MARKDOWN, reply_markup=entry_keyboard(e))


async def wotd_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    e = entry_of_the_day("vocab")
    if not e:
        await update.message.reply_text("No word of the day available.")
        return
    await update.message.reply_text(
        "*Ọ̀rọ̀ Òní — Word of the Day*\n\n" + format_entry(e),
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=entry_keyboard(e),
    )


async def potd_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    e = entry_of_the_day("owe")
    if not e:
        await update.message.reply_text("No proverb of the day available.")
        return
    await update.message.reply_text(
        "*Òwe Òní — Proverb of the Day*\n\n" + format_entry(e),
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=entry_keyboard(e),
    )


async def quiz_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    e = random_entry("njeomo")
    if not e:
        await update.message.reply_text("No quiz questions available right now.")
        return
    q = e.get("question_english") or e.get("yoruba") or "?"
    text = f"*Nje O Mọ?*\n\n{q}"
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=entry_keyboard(e, reveal=True))


async def search_entries(query: str):
    fts_query = " & ".join(query.split())
    res = sb.table("entries").select("*").fts("search_vector", fts_query).limit(5).execute()
    return res.data


async def search_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args)
    if not query:
        await update.message.reply_text("Usage: /search <word or phrase>")
        return
    await run_search(update, query)


async def free_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Any non-command message doubles as a search / 'ask a question' query."""
    await run_search(update, update.message.text)


async def run_search(update: Update, query: str):
    try:
        rows = await search_entries(query)
    except Exception as exc:  # noqa: BLE001
        log.exception("search failed")
        await update.message.reply_text("Search hit an error — try a shorter or different term.")
        return
    if not rows:
        await update.message.reply_text(
            "Kò sí àbájáde. No results — try a different word, or ask on WhatsApp/email (see /about)."
        )
        return
    for e in rows:
        await update.message.reply_text(format_entry(e), parse_mode=ParseMode.MARKDOWN, reply_markup=entry_keyboard(e))


async def favorites_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_res = sb.table("users").select("id").eq("telegram_id", update.effective_user.id).execute()
    if not user_res.data:
        await update.message.reply_text("You haven't saved any favorites yet — try /word or /proverb then tap ⭐.")
        return
    user_id = user_res.data[0]["id"]
    fav_res = (
        sb.table("favorites")
        .select("entries(*)")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(10)
        .execute()
    )
    if not fav_res.data:
        await update.message.reply_text("You haven't saved any favorites yet — try /word or /proverb then tap ⭐.")
        return
    for row in fav_res.data:
        e = row["entries"]
        if e:
            await update.message.reply_text(format_entry(e), parse_mode=ParseMode.MARKDOWN)


async def about_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "*Ọ̀NÀ* — a Yoruba language & culture archive.\n\n"
        "Entries are marked honestly: fieldwork-verified, sourced, or unverified/disputed where sources disagree.\n\n"
        "Site: https://apakose-ezekiel.github.io/ona-yoruba/\n"
        "Built by *Apákọsé Ezekiel Imoleayo*\n"
        "WhatsApp: https://wa.me/8183879878\n"
        "Email: apakosee@gmail.com\n"
        "LinkedIn: https://www.linkedin.com/in/apakose-ezekiel/\n"
        "X: https://x.com/Ogbeni_Imoleayo\n"
        "Hugging Face: https://huggingface.co/Apakose-Ezekiel",
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True,
    )


async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action, _, entry_id = query.data.partition(":")
    entry_id = int(entry_id)

    if action == "reveal":
        res = sb.table("entries").select("*").eq("id", entry_id).single().execute()
        e = res.data
        answer = e.get("drop_english") or e.get("drop_text") or "(no recorded answer)"
        yoruba_answer = e.get("drop_text")
        text = query.message.text_markdown_v2 if False else query.message.text
        new_text = text + "\n\n" + (f"{yoruba_answer}\n" if yoruba_answer else "") + answer
        await query.edit_message_text(new_text, reply_markup=entry_keyboard(e))

    elif action == "fav":
        upsert_user(update)
        user_res = sb.table("users").select("id").eq("telegram_id", update.effective_user.id).single().execute()
        user_id = user_res.data["id"]
        sb.table("favorites").upsert(
            {"user_id": user_id, "entry_id": entry_id}, on_conflict="user_id,entry_id"
        ).execute()
        await query.answer("Saved to favorites ⭐", show_alert=False)


def main():
    app = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
        .connect_timeout(20)
        .read_timeout(20)
        .get_updates_connect_timeout(20)
        .get_updates_read_timeout(20)
        .build()
    )
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("word", word_cmd))
    app.add_handler(CommandHandler("proverb", proverb_cmd))
    app.add_handler(CommandHandler("ifa", ifa_cmd))
    app.add_handler(CommandHandler("wotd", wotd_cmd))
    app.add_handler(CommandHandler("potd", potd_cmd))
    app.add_handler(CommandHandler("quiz", quiz_cmd))
    app.add_handler(CommandHandler("search", search_cmd))
    app.add_handler(CommandHandler("favorites", favorites_cmd))
    app.add_handler(CommandHandler("about", about_cmd))
    app.add_handler(CallbackQueryHandler(on_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, free_text))

    log.info("Ọ̀NÀ bot starting (polling)...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
