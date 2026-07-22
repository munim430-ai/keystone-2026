import csv

from keystone_voice.db import Database, normalize_bd_phone, infer_category


def test_normalize_bd_phone():
    assert normalize_bd_phone("+8801711004605") == "+8801711004605"
    assert normalize_bd_phone("01711004605") == "+8801711004605"
    assert normalize_bd_phone("8801711-004605") == "+8801711004605"
    assert normalize_bd_phone("1711004605") == "+8801711004605"
    assert normalize_bd_phone("0171100") is None       # too short
    assert normalize_bd_phone("+14155550123") is None  # not BD mobile
    assert normalize_bd_phone("") is None


def test_infer_category():
    assert infer_category("Dhaka Korean Language Center") == "korean"
    assert infer_category("British IELTS Academy") == "ielts"
    assert infer_category("Sunrise Visa Consultancy") == "visa"
    assert infer_category("Global Coaching") == "english"


def test_import_and_funnel(tmp_path):
    csv_path = tmp_path / "c.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Center Name", "Location (District)", "WhatsApp/Mobile", "Source URL"])
        w.writerow(["Alpha Korean Center", "Cumilla", "01711004605", "http://fb/a"])
        w.writerow(["Beta IELTS", "Rajshahi", "+8801812345678", "http://fb/b"])
        w.writerow(["Gamma", "Khulna", "not-a-number", "http://fb/c"])
        w.writerow(["Alpha Korean Center", "Cumilla", "01711004605", "dup"])  # duplicate phone

    db = Database(str(tmp_path / "t.db"))
    res = db.import_centers_csv(str(csv_path))
    assert res["added"] == 2
    assert res["duplicates"] == 1
    assert res["invalid"] == 1

    # korean center should outrank ielts by priority
    nxt = db.next_center(max_attempts=3)
    assert nxt["category"] == "korean"


def test_apply_outcome_progression(tmp_path):
    db = Database(str(tmp_path / "t.db"))
    db._exec("INSERT INTO centers(name,phone,status) VALUES(?,?,?)",
             ("X", "+8801711004605", "new"))
    cid = db.one("SELECT id FROM centers")["id"]
    db.apply_outcome(cid, "interested")
    assert db.one("SELECT status FROM centers WHERE id=?", (cid,))["status"] == "interested"
    # should not regress from interested back to contacted
    db.apply_outcome(cid, "answered")
    assert db.one("SELECT status FROM centers WHERE id=?", (cid,))["status"] == "interested"
    # dnc always wins
    db.apply_outcome(cid, "dnc")
    row = db.one("SELECT status,dnc FROM centers WHERE id=?", (cid,))
    assert row["dnc"] == 1 and row["status"] == "dnc"


def test_kill_switch(tmp_path):
    db = Database(str(tmp_path / "t.db"))
    assert db.killed is False
    db.set_killed(True)
    assert db.killed is True
    db.set_killed(False)
    assert db.killed is False


def test_attempts_exhaust(tmp_path):
    db = Database(str(tmp_path / "t.db"))
    db._exec("INSERT INTO centers(name,phone,status) VALUES(?,?,?)",
             ("X", "+8801711004605", "new"))
    cid = db.one("SELECT id FROM centers")["id"]
    for _ in range(3):
        db.mark_attempt(cid)
    assert db.one("SELECT status FROM centers WHERE id=?", (cid,))["status"] == "exhausted"
    assert db.next_center(max_attempts=3) is None
