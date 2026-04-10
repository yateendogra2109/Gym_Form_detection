from __future__ import annotations

import argparse
import sys
import time

import cv2

from gymcv.biomech.landmarks import compute_exercise_angles
from gymcv.config.exercises import EXERCISE_LABELS, SUPPORTED_EXERCISES
from gymcv.exercise_logic.fsm import RepCounterFSM
from gymcv.input.video_source import VideoSource
from gymcv.novelty.asymmetry import AsymmetryScorer
from gymcv.novelty.fatigue import FatigueDetector
from gymcv.novelty.scoring import FormScorer, GamificationEngine
from gymcv.pose.blazepose import BlazePoseEstimator
from gymcv.storage.sqlite_logger import SessionLogger
from gymcv.ui.overlay import draw_stats


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Smart Gym — live session (exercise selection is in Streamlit: streamlit run src/dashboard.py)."
    )
    parser.add_argument("--camera", type=int, default=0, help="Webcam device index when using live capture")
    parser.add_argument(
        "--video",
        default=None,
        metavar="PATH",
        help="If set, skip the UI and run from this video file (still use --exercise)",
    )
    parser.add_argument(
        "--exercise",
        default=None,
        choices=list(SUPPORTED_EXERCISES.keys()),
        help="Required with --video; optional with --no-launcher for webcam without UI",
    )
    parser.add_argument(
        "--no-launcher",
        action="store_true",
        help="Skip exercise picker; use --exercise with live --camera (for scripts/headless)",
    )
    parser.add_argument("--db_path", default="gymcv.db", help="SQLite database path")
    return parser.parse_args()


def run_live_session(exercise_name: str, source: int | str, db_path: str) -> int:
    cfg = SUPPORTED_EXERCISES[exercise_name]
    video = VideoSource(source=source)
    pose = BlazePoseEstimator()
    rep_counter = RepCounterFSM(
        top_angle=cfg.top_angle,
        bottom_angle=cfg.bottom_angle,
        smoothing_window=cfg.smoothing_window,
        max_angle_guard=cfg.max_angle_guard,
        min_angle_guard=cfg.min_angle_guard,
    )
    fatigue_detector = FatigueDetector(cfg.fatigue_rom_drop_pct, cfg.fatigue_velocity_drop_pct)
    asymmetry = AsymmetryScorer()
    scorer = FormScorer()
    game = GamificationEngine()
    logger = SessionLogger(db_path)

    prev_time = time.time()
    prev_main_angle = None
    fatigue_events = 0
    rep_asym_scores: list[float] = []
    last_asym_score: float | None = None
    last_fatigue = False
    last_rep_score = 0.0
    last_asym_alert = False

    display_name = EXERCISE_LABELS.get(exercise_name, exercise_name)

    while True:
        ok, frame = video.read()
        if not ok:
            break

        result = pose.process(frame)
        lm = result.pose_landmarks
        pose.draw(frame, lm)

        if lm is not None and lm.landmark is not None:
            landmarks = lm.landmark
            reading = compute_exercise_angles(
                landmarks, pose.landmarks_enum.__members__, exercise_name, cfg.visibility_threshold
            )
            if reading is not None:
                if prev_main_angle is None:
                    displacement = 0.0
                else:
                    displacement = abs(reading.main_angle - prev_main_angle)
                prev_main_angle = reading.main_angle

                _, _, smoothed_angle, rep_completed = rep_counter.update(reading.main_angle)
                fatigue_detector.update_frame(smoothed_angle, displacement, rep_counter.in_concentric)

                if cfg.symmetry_enabled:
                    last_asym_score, asym_alert = asymmetry.score(reading.left_angle, reading.right_angle)
                else:
                    last_asym_score, asym_alert = (None, False)

                if rep_completed:
                    last_fatigue, rom, velocity = fatigue_detector.close_rep()
                    if last_fatigue:
                        fatigue_events += 1
                    last_rep_score = scorer.rep_score(
                        smoothed_angle,
                        (cfg.ideal_bottom_min, cfg.ideal_bottom_max),
                        (cfg.ideal_top_min, cfg.ideal_top_max),
                    )
                    xp_gained = game.register_rep(last_rep_score)
                    if last_asym_score is not None:
                        rep_asym_scores.append(last_asym_score)
                    logger.log_rep(
                        exercise=exercise_name,
                        rep_index=rep_counter.count,
                        form_score=last_rep_score,
                        asymmetry_score=last_asym_score,
                        fatigue_flag=last_fatigue,
                        rom=rom,
                        velocity=velocity,
                        xp_gained=xp_gained,
                    )
                # Update last_asym_alert directly from scorer output.
                # The scorer has sticky hold logic — it returns True for ~15
                # frames after the last trigger, so last_asym_alert stays
                # True long enough to be visible even during landmark flicker.
                last_asym_alert = asym_alert

        current_time = time.time()
        fps = 1.0 / max(current_time - prev_time, 1e-6)
        prev_time = current_time
        display_frame = draw_stats(
            frame,
            rep_counter.count,
            rep_counter.stage,
            rep_counter.last_angle,
            fps,
            display_name,
            last_rep_score,
            last_asym_score,
            last_fatigue,
            game.xp,
            last_asym_alert,
        )
        cv2.imshow("Smart Gym — Live", display_frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    pose.close()
    avg_asym = (sum(rep_asym_scores) / len(rep_asym_scores)) if rep_asym_scores else None
    logger.log_session(
        exercise=exercise_name,
        reps=rep_counter.count,
        avg_form_score=game.session_score,
        avg_asymmetry_score=avg_asym,
        fatigue_events=fatigue_events,
        total_xp=game.xp,
    )
    logger.close()
    video.release()
    cv2.destroyAllWindows()
    return 0


def main() -> int:
    args = parse_args()

    if args.video is not None:
        exercise = args.exercise
        if exercise is None:
            print("With --video you must pass --exercise <name>.", file=sys.stderr)
            return 2
        return run_live_session(exercise, args.video, args.db_path)

    if args.no_launcher:
        exercise = args.exercise
        if exercise is None:
            print("With --no-launcher you must pass --exercise <name>.", file=sys.stderr)
            return 2
        return run_live_session(exercise, args.camera, args.db_path)

    print(
        "Choose your exercise in the web app, then click Start:\n"
        "  streamlit run src/dashboard.py\n\n"
        "CLI-only webcam (no Streamlit):\n"
        "  python src/main.py --no-launcher --exercise squat --camera 0",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
