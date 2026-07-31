"""In-process smoke test of the HTTP API (no sockets, no background procs)."""
from fastapi.testclient import TestClient

from keystone_voice.app import create_app
from keystone_voice.config import Config


def main() -> None:
    cfg = Config.load()
    cfg.call_hours_start, cfg.call_hours_end, cfg.min_gap_seconds = 0, 24, 0
    cfg.daily_call_cap = 50
    app = create_app(cfg)
    with TestClient(app) as c:
        print("twilio_configured:", c.get("/health").json()["twilio_configured"])
        s = c.get("/api/stats").json()
        print("gate:", s["can_call_now"], "|", s["call_gate_reason"])
        print("dial1:", c.post("/api/call-next").json())
        print("dial2:", c.post("/api/call-next").json())
        for cl in c.get("/api/calls?limit=5").json():
            print("  call", cl["id"], cl["center_name"][:30], cl["status"], "/", cl["outcome"])
        print("kill:", c.post("/api/kill").json())
        print("dial while killed:", c.post("/api/call-next").json())
        print("resume:", c.post("/api/resume").json())


if __name__ == "__main__":
    main()
