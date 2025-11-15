import os
import sys
import asyncio
import logging

from telethon import TelegramClient, events
from telethon.tl import types
from dotenv import load_dotenv
from telethon.errors import SessionPasswordNeededError


def parse_bool(s: str) -> bool:
    return str(s).strip().lower() in ("1", "true", "yes", "y", "on")


def parse_entity_spec(s: str):
    v = s.strip()
    if v.lstrip("-").isdigit():
        try:
            return int(v)
        except Exception:
            pass
    return v


async def main():
    load_dotenv()

    api_id = os.getenv("TG_API_ID")
    api_hash = os.getenv("TG_API_HASH")
    source_chat = os.getenv("SOURCE_CHAT")
    target_chat = os.getenv("TARGET_CHAT")
    forward_mode = (os.getenv("FORWARD_MODE", "forward")).strip().lower()
    filter_from_username = (os.getenv("FILTER_FROM_USERNAME", "").strip().lstrip("@").lower())
    skip_service = parse_bool(os.getenv("SKIP_SERVICE_MESSAGES", "true"))
    log_level = (os.getenv("LOG_LEVEL", "INFO")).upper()
    phone = os.getenv("TG_PHONE")

    try:
        logging.basicConfig(level=getattr(logging, log_level, logging.INFO), format="%(asctime)s %(levelname)s %(message)s")
    except Exception:
        logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    if not api_id or not api_hash or not source_chat or not target_chat:
        logging.error("Missing required environment variables.")
        sys.exit(1)

    if forward_mode not in ("forward", "copy"):
        logging.warning("FORWARD_MODE=%s is not supported, using forward", forward_mode)

    api_id_int = int(api_id)
    client = TelegramClient("forwarder", api_id_int, api_hash)
    await client.connect()

    if not await client.is_user_authorized():
        if not phone:
            logging.error("No TG_PHONE provided and not authorized. Cannot sign in.")
            sys.exit(1)
        # Send code and sign in
        await client.send_code_request(phone)
        code = input("Enter the login code you received: ")
        try:
            await client.sign_in(phone=phone, code=code)
        except SessionPasswordNeededError:
            pwd = os.getenv("TG_PASSWORD")
            if not pwd:
                logging.error("Two-step verification enabled but TG_PASSWORD not set in .env.")
                sys.exit(1)
            await client.sign_in(password=pwd)

    source_spec = parse_entity_spec(source_chat)
    target_spec = parse_entity_spec(target_chat)
    source_entity = await client.get_input_entity(source_spec)
    target_entity = await client.get_input_entity(target_spec)

    async def on_new_message(event):
        m = event.message
        if skip_service and isinstance(m, types.MessageService):
            return
        if filter_from_username:
            sender = await event.get_sender()
            username = (getattr(sender, "username", None) or "").lower()
            if username != filter_from_username:
                return
        try:
            if forward_mode == "forward":
                await m.forward_to(target_entity)
                logging.info("Forwarded message %s", m.id)
            else:
                if m.media:
                    try:
                        await client.send_file(target_entity, m.media, caption=m.message or None, formatting_entities=m.entities)
                        logging.info("Copied media message %s", m.id)
                    except Exception:
                        try:
                            data = await m.download_media(file=bytes)
                            await client.send_file(target_entity, data, caption=m.message or None, formatting_entities=m.entities)
                            logging.info("Copied media message via reupload %s", m.id)
                        except Exception:
                            logging.exception("Copy media failed")
                else:
                    await client.send_message(target_entity, m.message or "", formatting_entities=m.entities)
                    logging.info("Copied text message %s", m.id)
        except Exception:
            logging.exception("Send failed")

    client.add_event_handler(on_new_message, events.NewMessage(chats=source_entity))

    logging.info("Running. Forwarding from %s to %s", str(source_chat), str(target_chat))
    await client.run_until_disconnected()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
