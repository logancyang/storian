import numpy as np

from storian.check import check_sequence
from storian.media import parse_tc, phase_shift, summarize_motion, write_slog3_lut
from storian.project import Project, write_json


def test_parse_tc():
    assert parse_tc(12.5) == 12.5
    assert parse_tc("01:02.5") == 62.5
    assert parse_tc("1:00:00") == 3600


def test_phase_shift_detects_pan():
    rng = np.random.default_rng(0)
    a = rng.random((72, 128)).astype(np.float32)
    b = np.roll(a, -5, axis=1)  # content moves left => camera pans right
    assert phase_shift(a, b) == (-5, 0)
    sig = [{"brightness": .5, "sharpness": 5}] + [{"brightness": .5, "sharpness": 5, "change": .05, "shift": [-5, 0]}] * 3
    assert summarize_motion(sig)["camera_hint"] == "pan-right"


def test_slog3_lut_maps_mid_grey(tmp_path):
    lut = tmp_path / "x.cube"
    write_slog3_lut(lut, size=17)
    rows = [l for l in lut.read_text().splitlines() if l and l[0].isdigit()]
    assert len(rows) == 17 ** 3
    assert rows[0] == "0.000000 0.000000 0.000000"


def make_project(tmp_path, shots):
    p = Project(tmp_path)
    write_json(p.config_path, {"name": "t", "footage_dir": str(tmp_path), "target_minutes": 0.25})
    write_json(p.clips_path, [{"id": "A", "path": "A.mp4", "duration": 20.0}, {"id": "B", "path": "B.mp4", "duration": 10.0}])
    write_json(p.labels_dir / "A.json", {"shot_size": "WS", "focal_feel": "wide", "quality": 4})
    write_json(p.labels_dir / "B.json", {"shot_size": "WS", "focal_feel": "wide", "quality": 4})
    write_json(p.sequence_path, {"title": "t", "theme": "t", "mood": "m", "central_idea": "c",
                                 "acts": [{"title": "one", "shots": shots}]})
    return p


def test_check_flags_errors_and_lints(tmp_path):
    p = make_project(tmp_path, [
        {"id": "s1", "clip": "A", "in": 1, "out": 4, "cut": "hard"},
        {"id": "s2", "clip": "B", "in": 2, "out": 5, "cut": "hard"},       # same size + focal
        {"id": "s3", "clip": "B", "in": 5, "out": 12, "cut": "hard"},      # past clip end
        {"id": "s4", "clip": "Z", "in": 0, "out": 1},                      # unknown clip
    ])
    r = check_sequence(p)
    assert any("s3" in e for e in r["errors"])
    assert any("unknown clip Z" in e for e in r["errors"])
    assert any(w.startswith("s2: same size") for w in r["warnings"])


def test_check_accepts_motivated_cut(tmp_path):
    p = make_project(tmp_path, [
        {"id": "s1", "clip": "A", "in": 1, "out": 8, "cut": "hard"},
        {"id": "s2", "clip": "B", "in": 2, "out": 9, "cut": "cut-on-motion"},
    ])
    r = check_sequence(p)
    assert r["errors"] == [] and r["warnings"] == []
    assert r["stats"]["shots"] == 2


def test_auto_scenes_split_on_time_and_place():
    from storian.coverage import auto_scenes
    clips = [{"id": "A", "duration": 10, "recorded_at": "2025:11:13 10:00:00"},
             {"id": "B", "duration": 10, "recorded_at": "2025:11:13 10:02:00"},   # same place, 2 min later
             {"id": "C", "duration": 10, "recorded_at": "2025:11:13 10:10:00"},   # new place after 8 min
             {"id": "D", "duration": 10, "recorded_at": "2025:11:13 12:00:00"}]   # back after 2 h
    labels = {"A": {"location": "Star Ferry pier, Tsim Sha Tsui"}, "B": {"location": "Star Ferry deck"},
              "C": {"location": "Dim sum restaurant"}, "D": {"location": "Dim sum restaurant"}}
    assert [s["clips"] for s in auto_scenes(clips, labels)] == [["A", "B"], ["C", "D"]]


def test_scene_gaps_flags_missing_coverage():
    from storian.coverage import scene_gaps
    wides = [{"shot_size": "WS", "focal_feel": "wide", "angle": "eye", "camera_move": "static",
              "quality": 4, "story_role": ["establishing"]}] * 4
    gaps = scene_gaps(wides)
    assert {"no-close", "no-detail", "no-people", "one-focal-wide", "flat-angle", "no-movement"} <= set(gaps)
    assert scene_gaps(wides[:2]) == ["thin"]
    assert scene_gaps([{**wides[0], "quality": 2}] * 4) == ["unusable"]


def test_coverage_review_overrides_scenes(tmp_path):
    from storian.coverage import analyze
    p = make_project(tmp_path, [{"id": "s1", "clip": "A", "in": 1, "out": 4}])
    write_json(p.coverage_path, {"summary": "x", "scenes": [
        {"id": "sc01", "name": "Pier", "clips": ["A", "B"], "verdict": "v",
         "needs": [{"shot": "CU hands", "size": "CU", "priority": 1}]},
        {"id": "sc02", "name": "Ghost", "clips": ["Z"]}]})
    r = analyze(p)
    assert r["reviewed"] and r["scenes"][0]["name"] == "Pier" and r["scenes"][0]["needs"][0]["shot"] == "CU hands"
    assert r["scenes"][0]["used"] == ["s1"]
    assert any("unknown clip Z" in e for e in r["errors"])


def test_estimate_bpm_on_a_click_track():
    from storian.music import SR, estimate_bpm
    y = np.zeros(SR * 30, np.float32)
    rng = np.random.default_rng(0)
    step = SR * 60 / 96
    for k in range(int(len(y) / step) - 1):
        i = int(k * step)
        y[i:i + 400] += np.hanning(400) * rng.normal(0, 1, 400)
    assert abs(estimate_bpm(y) - 96) < 1.5


def test_music_check_flags_unknown_tracks(tmp_path):
    from storian.music import check, load
    p = make_project(tmp_path, [{"id": "s1", "clip": "A", "in": 1, "out": 4}])
    write_json(p.music_path, {"tracks": [{"id": "t1"}], "cues": [
        {"id": "m1", "acts": [0], "candidates": [{"track": "t1"}, {"track": "t9"}], "chosen": "t1"},
        {"id": "m2", "acts": [3], "candidates": []}]})
    errs = check(p, load(p))
    assert any("unknown track t9" in e for e in errs) and any("m2: act index" in e for e in errs)


def test_scene_when_uses_shoot_timezone():
    from storian.coverage import scene_when
    w = scene_when([{"recorded_at": "2025:11:13 15:17:19-08:00"}], [{"time_of_day": "dawn"}], "Asia/Hong_Kong")
    assert (w["date"], w["start"], w["tz"]) == ("Fri 14 Nov 2025", "07:17", "HKT")


def test_publish_snapshot_holds_only_what_the_page_shows(tmp_path):
    from storian.publish import build, frame_name, worker_name
    assert frame_name([0.083, 1.084, 2.085], 1.5) == "t00001.084.jpg"  # same pick as frameUrl() in the page
    assert frame_name([0.083, 1.084, 2.085], 0.0) == "t00000.083.jpg"
    p = Project(tmp_path)
    write_json(p.config_path, {"name": "2026 Lisbon!", "footage_dir": str(tmp_path)})
    write_json(p.clips_path, [{"id": "C1", "duration": 9.0}])
    (p.frames_dir / "C1").mkdir(parents=True)
    ts = [0.5, 2.5, 4.5, 6.5, 8.5]
    for t in ts:
        (p.frames_dir / "C1" / f"t{t:09.3f}.jpg").write_bytes(b"jpg")
    write_json(p.frames_dir / "C1" / "index.json", {"clip": "C1", "frames": [{"t": t} for t in ts]})
    write_json(p.sequence_path, {"acts": [{"title": "a", "shots": [{"id": "s1", "clip": "C1", "in": 2.0, "out": 4.0}]}]})
    info = build(p, tmp_path / ".publish")
    pub = tmp_path / ".publish" / "public"
    frames = sorted(x.name for x in (pub / "media" / "frames" / "C1").iterdir())
    assert frames == ["t00002.500.jpg", "t00004.500.jpg"]  # s1's thumbnails and the Library's middle frame, not all five
    assert (pub / "api" / "project.json").exists() and (pub / "sw.js").read_text().count(info["published"]) == 1
    assert worker_name(p) == "storian-2026-lisbon"


def test_watcher_publishes_after_a_change_settles(tmp_path, monkeypatch):
    import os, time
    from storian import publish as pub
    monkeypatch.setattr(pub, "CONFIG", tmp_path / "hosted.json")
    p = Project(tmp_path / "proj")
    write_json(p.config_path, {"name": "t", "footage_dir": str(tmp_path)})
    old = time.time() - 600
    os.utime(p.config_path, (old, old))
    assert pub.due(p, settle=90)  # never published
    pub.save_config({"workers": {pub.worker_name(p): {"version": old}}})
    assert not pub.due(p, settle=90)  # nothing changed since
    write_json(p.sequence_path, {"acts": []})
    assert not pub.due(p, settle=90)  # changed, but the agent may still be writing
    assert pub.due(p, settle=0)
