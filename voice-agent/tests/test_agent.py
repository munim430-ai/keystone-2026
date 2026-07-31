import pytest

from keystone_voice.agent import SalesAgent
from keystone_voice.config import Config
from keystone_voice.db import Database
from keystone_voice.llm.mock import MockLLM


def _setup(tmp_path):
    cfg = Config.load()
    cfg.db_path = str(tmp_path / "t.db")
    cfg.demo_mode = True
    db = Database(cfg.db_path)
    center = {"id": 1, "name": "টেস্ট কোরিয়ান সেন্টার", "district": "কুমিল্লা",
              "category": "korean", "phone": "+8801711004605", "attempts": 0, "notes": ""}
    db._exec("INSERT INTO centers(id,name,district,category,phone) VALUES(?,?,?,?,?)",
             (1, center["name"], center["district"], center["category"], center["phone"]))
    call_id = db.create_call(1, center["phone"])
    return cfg, db, SalesAgent(cfg, db, MockLLM(), center, call_id)


@pytest.mark.asyncio
async def test_agent_greets_and_pitches(tmp_path):
    cfg, db, agent = _setup(tmp_path)
    reply = await agent.respond("জি বলছি, কে বলছেন?")
    assert reply
    assert "কিস্টোন" in reply or "মায়া" in reply


@pytest.mark.asyncio
async def test_agent_captures_whatsapp(tmp_path):
    cfg, db, agent = _setup(tmp_path)
    await agent.respond("কে বলছেন?")
    await agent.respond("কমিশন কত?")
    await agent.respond("আচ্ছা WhatsApp এ পাঠান, ০১৭১১০০০০০০")
    assert agent.state.whatsapp is not None
    row = db.one("SELECT whatsapp,status FROM centers WHERE id=1")
    assert row["status"] == "whatsapp_captured"


@pytest.mark.asyncio
async def test_agent_ends_call(tmp_path):
    cfg, db, agent = _setup(tmp_path)
    await agent.respond("কে বলছেন?")
    await agent.respond("ঠিক আছে, ধন্যবাদ, রাখি")
    assert agent.state.ended is True


@pytest.mark.asyncio
async def test_output_has_no_markdown(tmp_path):
    cfg, db, agent = _setup(tmp_path)
    reply = await agent.respond("কে বলছেন?")
    for junk in ("*", "#", "`", "_", "[", "]"):
        assert junk not in reply
