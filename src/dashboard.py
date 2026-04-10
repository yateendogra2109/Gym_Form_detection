from __future__ import annotations

import sqlite3
import subprocess
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from gymcv.config.exercises import exercise_select_options
from gymcv.storage.sqlite_logger import SessionLogger

# Project root (folder that contains `src/`), for subprocess cwd and DB paths
_SRC_DIR = Path(__file__).resolve().parent
_PROJ_ROOT = _SRC_DIR.parent
_MAIN_SCRIPT = _SRC_DIR / "main.py"


def ensure_db_schema(db_path: str) -> None:
    """Create SQLite tables if missing so Analytics queries never fail on a fresh DB."""
    logger = SessionLogger(db_path)
    logger.close()


def _resolve_db_path(db_path: str) -> str:
    p = Path(db_path).expanduser()
    if not p.is_absolute():
        p = _PROJ_ROOT / p
    return str(p.resolve())


def load_df(db_path: str, query: str) -> pd.DataFrame:
    """Return query results, or an empty DataFrame if the DB or table does not exist yet."""
    if not Path(db_path).exists():
        return pd.DataFrame()
    con = sqlite3.connect(db_path)
    try:
        return pd.read_sql_query(query, con)
    except (sqlite3.OperationalError, pd.errors.DatabaseError) as exc:
        if "no such table" in str(exc).lower():
            return pd.DataFrame()
        raise
    finally:
        con.close()


def render_live_tab(db_path: str) -> None:
    st.subheader("Live workout")
    st.caption(
        "Pick an exercise, then start. A separate **Smart Gym — Live** window opens (not inside the browser) "
        "with your webcam, pose overlay, reps, form score, fatigue, asymmetry, and XP. Press **q** in that window "
        "to stop and save to the database. If nothing appears, check the console window that may open on Windows, "
        "or run `python src/main.py --no-launcher --exercise bicep_curl` in a terminal to see errors."
    )

    options = exercise_select_options()
    labels = [label for _, label in options]
    keys = [key for key, _ in options]

    choice = st.selectbox("Exercise", range(len(labels)), format_func=lambda i: labels[i])
    exercise_key = keys[choice]

    camera = st.number_input("Webcam index", min_value=0, max_value=9, value=0, step=1)

    if st.button("Open webcam & start session", type="primary"):
        db_abs = _resolve_db_path(db_path)
        cmd = [
            sys.executable,
            str(_MAIN_SCRIPT),
            "--no-launcher",
            "--exercise",
            exercise_key,
            "--camera",
            str(int(camera)),
            "--db_path",
            db_abs,
        ]
        popen_kwargs: dict = {"cwd": str(_PROJ_ROOT)}
        if sys.platform == "win32":
            # Extra console so import/runtime errors (e.g. wrong mediapipe) are visible.
            popen_kwargs["creationflags"] = getattr(subprocess, "CREATE_NEW_CONSOLE", 0)

        try:
            subprocess.Popen(cmd, **popen_kwargs)
        except OSError as e:
            st.error(f"Could not start session: {e}")
            return
        st.success(
            "Session process started. Bring the **Smart Gym — Live** window to the front. "
            "When finished, press **q** there, then open the **Analytics** tab and refresh if needed."
        )


def render_analytics_tab(db_path: str) -> None:
    st.subheader("Session analytics")

    rep_df = load_df(db_path, "SELECT * FROM rep_events ORDER BY id")
    sess_df = load_df(db_path, "SELECT * FROM session_summary ORDER BY id")

    if rep_df.empty and sess_df.empty:
        st.info("No rows in this database yet. Run a live session from the **Live workout** tab first.")
        return

    if not sess_df.empty:
        last = sess_df.iloc[-1]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Last session reps", int(last["reps"]))
        c2.metric("Last avg form", f'{last["avg_form_score"]:.1f}')
        c3.metric("Last fatigue events", int(last["fatigue_events"]))
        c4.metric("Last total XP", int(last["total_xp"]))

    if not rep_df.empty:
        st.markdown("#### Rep-by-rep trends")
        fig1 = px.line(rep_df, x="id", y="form_score", color="exercise", title="Form score trend")
        st.plotly_chart(fig1, use_container_width=True)
        if rep_df["asymmetry_score"].notna().any():
            fig2 = px.line(
                rep_df.dropna(subset=["asymmetry_score"]),
                x="id",
                y="asymmetry_score",
                color="exercise",
                title="Asymmetry score trend",
            )
            st.plotly_chart(fig2, use_container_width=True)
        fig3 = px.bar(rep_df, x="id", y="xp_gained", color="exercise", title="XP per rep")
        st.plotly_chart(fig3, use_container_width=True)

    if not sess_df.empty:
        st.markdown("#### Session summary")
        st.dataframe(sess_df, use_container_width=True)


def main() -> None:
    st.set_page_config(page_title="Smart Gym", layout="wide")
    st.title("Smart Gym")

    db_path = st.sidebar.text_input("SQLite database path", value="gymcv.db", help="Relative paths are resolved from the project folder.")
    db_resolved = _resolve_db_path(db_path)
    ensure_db_schema(db_resolved)

    tab_live, tab_analytics = st.tabs(["Live workout", "Analytics"])

    with tab_live:
        render_live_tab(db_path)

    with tab_analytics:
        render_analytics_tab(db_resolved)


if __name__ == "__main__":
    main()
