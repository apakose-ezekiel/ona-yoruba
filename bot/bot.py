"""
Ọ̀NÀ Telegram bot (@OnaYorubaBot) — same Supabase database as the site, so
every domain (words, proverbs, Ifá, quiz, search) has feature parity here.
Uses the service_role key server-side only; never exposed to users.
"""
import logging
import os
import random
import threading
from datetime import date
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, Update
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

# Domain buttons mirror the site's /entries/ filter chips exactly, so the
# bot covers every domain the site does, not just a handful.
BTN_WORD = "📝 Ọ̀rọ̀ — Vocabulary"
BTN_PROVERB = "📖 Òwe — Proverbs"
BTN_IFA = "🔮 Ifá"
BTN_ORISA = "🛕 Òrìṣà"
BTN_ORIKI = "👑 Oríkì"
BTN_AROKO = "📯 Àrokò"
BTN_ETHICS = "⚖️ Ìwà — Ethics"
BTN_DISCOURSE = "💬 Discourse"
BTN_QUIZ = "🎮 Nje O Mọ — Quiz"
BTN_WOTD = "🌅 Ọ̀rọ̀ Òní — Word of the Day"
BTN_POTD = "🌇 Òwe Òní — Proverb of the Day"
BTN_SEARCH = "🔍 Wá — Search"
BTN_FAVORITES = "⭐ Favorites"
BTN_ABOUT = "ℹ️ About"
BTN_HELP = "❓ Help"

MAIN_KEYBOARD = ReplyKeyboardMarkup(
    [
        [BTN_WORD, BTN_PROVERB],
        [BTN_IFA, BTN_ORISA],
        [BTN_ORIKI, BTN_AROKO],
        [BTN_ETHICS, BTN_DISCOURSE],
        [BTN_QUIZ],
        [BTN_WOTD, BTN_POTD],
        [BTN_SEARCH, BTN_FAVORITES],
        [BTN_ABOUT, BTN_HELP],
    ],
    resize_keyboard=True,
)

AWAITING_SEARCH = "awaiting_search"

HELP_TEXT = (
    "*Ọ̀NÀ — Yoruba words, proverbs, Ifá/Odù, and culture*\n\n"
    "Every button below covers a domain from the site — Vocabulary, Proverbs, "
    "Ifá, Òrìṣà, Oríkì, Àrokò, Ethics, Discourse, plus Quiz, Word/Proverb of "
    "the Day, Search, and Favorites.\n\n"
    "Type any question or word and I'll search for it, even if it's not exact "
    "— closest matches come back instead of nothing.\n\n"
    "Same archive as the onayoruba site (link in /about) — anything added there shows up here too."
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
    context.user_data[AWAITING_SEARCH] = False
    await update.message.reply_text(
        f"Ẹ nlẹ́, {update.effective_user.first_name}! Ọ̀NÀ ń kí ẹ.\n\n" + HELP_TEXT,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=MAIN_KEYBOARD,
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(HELP_TEXT, parse_mode=ParseMode.MARKDOWN, reply_markup=MAIN_KEYBOARD)


def make_domain_handler(domain: str | list[str], empty_msg: str):
    """One handler generator for every domain button (word/proverb/ifa/orisa/
    oriki/aroko/ethics/discourse) instead of near-duplicate functions."""

    async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        e = random_entry(domain)
        if not e:
            await update.message.reply_text(empty_msg)
            return
        await update.message.reply_text(
            format_entry(e), parse_mode=ParseMode.MARKDOWN, reply_markup=entry_keyboard(e)
        )

    return handler


word_cmd = make_domain_handler("vocab", "No words available right now.")
proverb_cmd = make_domain_handler("owe", "No proverbs available right now.")
ifa_cmd = make_domain_handler("ifa", "No Ifá entries available right now.")
orisa_cmd = make_domain_handler("orisa", "No Òrìṣà entries available right now.")
oriki_cmd = make_domain_handler("oriki", "No oríkì entries available right now.")
aroko_cmd = make_domain_handler("aroko", "No àrokò entries available right now.")
ethics_cmd = make_domain_handler("ethics", "No ethics entries available right now.")
discourse_cmd = make_domain_handler("discourse", "No discourse entries available right now.")


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
    res = sb.rpc("search_entries", {"q": query, "max_results": 6}).execute()
    return res.data


async def search_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args)
    if not query:
        await update.message.reply_text("Usage: /search <word or phrase>")
        return
    await run_search(update, query)


async def free_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Routes menu-button taps, then falls back to search for anything else
    (this is what makes free-text 'ask a question' messages work)."""
    text = update.message.text

    button_routes = {
        BTN_WORD: word_cmd,
        BTN_PROVERB: proverb_cmd,
        BTN_IFA: ifa_cmd,
        BTN_ORISA: orisa_cmd,
        BTN_ORIKI: oriki_cmd,
        BTN_AROKO: aroko_cmd,
        BTN_ETHICS: ethics_cmd,
        BTN_DISCOURSE: discourse_cmd,
        BTN_QUIZ: quiz_cmd,
        BTN_WOTD: wotd_cmd,
        BTN_POTD: potd_cmd,
        BTN_FAVORITES: favorites_cmd,
        BTN_ABOUT: about_cmd,
        BTN_HELP: help_cmd,
    }
    if text in button_routes:
        context.user_data[AWAITING_SEARCH] = False
        await button_routes[text](update, context)
        return

    if text == BTN_SEARCH:
        context.user_data[AWAITING_SEARCH] = True
        await update.message.reply_text("Kọ ohun tí o fẹ́ wá sí ìsàlẹ̀ yìí — type what you'd like to search for.")
        return

    context.user_data[AWAITING_SEARCH] = False
    await run_search(update, text)


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


def start_health_server():
    """Render's free tier is Web Services only (no free background workers),
    which requires binding to $PORT and responding to health checks. This
    runs in a daemon thread alongside the polling loop; harmless locally
    where PORT isn't set."""
    port = os.environ.get("PORT")
    if not port:
        return

    class Health(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok")

        def log_message(self, *args):
            pass  # keep the bot's own logging clean

    server = HTTPServer(("0.0.0.0", int(port)), Health)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    log.info(f"Health check server listening on :{port}")


def main():
    start_health_server()
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
    app.add_handler(CommandHandler("orisa", orisa_cmd))
    app.add_handler(CommandHandler("oriki", oriki_cmd))
    app.add_handler(CommandHandler("aroko", aroko_cmd))
    app.add_handler(CommandHandler("ethics", ethics_cmd))
    app.add_handler(CommandHandler("discourse", discourse_cmd))
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
