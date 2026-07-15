"""
Streamlit user interface – all UI rendering and interaction logic.

This module imports business logic from other ``app.*`` modules and wires
them together with Streamlit widgets.  No blocking ``time.sleep()`` calls
are used; instead we rely on ``st.rerun()`` and session state for
non-blocking refresh loops.
"""

from __future__ import annotations

import os
import time

import streamlit as st

from app.config import (
    DOWNLOAD_DIR,
    STATIC_DIR,
    Status,
    UI_REFRESH_DELAY,
    AUTO_START_NOTICE_DELAY,
    CACHE_POLL_ATTEMPTS,
    CACHE_POLL_ATTEMPTS_AUTO,
)
from app.queue_manager import (
    load_queue,
    save_queue,
    update_task,
    is_any_downloading,
    find_next_not_started,
    finished_task_urls,
    remove_tasks,
)
from app.downloader import (
    normalize_id,
    parse_display_name,
    find_mrjet_cache_folders,
    poll_for_cache_folder,
    launch_mrjet,
    step_task,
)


# ---------------------------------------------------------------------------
# Page & sidebar setup (called once per session)
# ---------------------------------------------------------------------------

def setup_page() -> None:
    """Configure Streamlit page (must be the first Streamlit command)."""
    st.set_page_config(
        page_title="MrJet WebGUI",
        page_icon="random",
        layout="centered",
        initial_sidebar_state="auto",
    )
    # Ensure directories exist
    if not os.path.exists(STATIC_DIR):
        os.makedirs(STATIC_DIR)

    # Initialise queue in session state
    if "download_queue" not in st.session_state:
        st.session_state.download_queue = load_queue()


# ---------------------------------------------------------------------------
# Main render function
# ---------------------------------------------------------------------------

def render() -> None:
    """
    Full UI render + event loop.  Called once per Streamlit re-run.
    """
    queue: dict = st.session_state.download_queue

    # ---- Title & input area ----
    st.title("MrJet WebGUI")

    st.text_area(
        label="Enter one or more Video IDs / URLs",
        placeholder=(
            "You can enter multiple items separated by commas, spaces or newlines.\n"
            "e.g.,\nwaaa-361, ssis-001"
        ),
        key="url_input_val",
    )

    add_col, start_col = st.columns((1, 5))
    with add_col:
        add_pressed = st.button("Add", use_container_width=True)
    with start_col:
        start_pressed = st.button("Start next queued task", use_container_width=True)

    # ---- Step ALL downloading / fixing tasks (non-blocking state machine) ----
    for url, task in list(queue.items()):
        step_task(url, task, queue)

    # Persist after any state changes
    save_queue(queue)

    # ---- Queue display ----
    st.markdown("---")
    if not queue:
        st.info("The download queue is empty.")
    else:
        for url, task in queue.items():
            main_cols = st.columns((5, 3, 2))
            main_cols[0].markdown(f'**ID:** [{task["DisplayName"]}]({url})')
            main_cols[1].text(f"Created: {task['Created Date']}")
            main_cols[2].markdown(f'**{task["Status"]}** {task.get("Log", "")}')
            st.text("Download Progress:")
            if task["Status"] in (Status.COMPLETED, Status.FIXING):
                st.progress(1.0)
            else:
                st.progress(task.get("Progress_Download", 0.0))
            st.markdown("---")

    # ---- Handle "Add" button ----
    if add_pressed and st.session_state.url_input_val:
        _handle_add(queue)

    # ---- Handle "Start next queued task" button ----
    if start_pressed:
        _handle_start_next(queue)

    # ---- Utils section ----
    with st.expander("Utils", expanded=False):
        if st.button("Clean finished tasks"):
            _handle_clean(queue)

    # ---- Auto-refresh while downloading ----
    if is_any_downloading(queue):
        time.sleep(UI_REFRESH_DELAY)
        st.rerun()
    else:
        # ---- Auto-start next task when idle ----
        _auto_start_next_if_idle(queue)


# ---------------------------------------------------------------------------
# Shared launch logic
# ---------------------------------------------------------------------------

def _start_task(queue: dict, url: str) -> None:
    """
    Launch the task at *url*: start mrjet and set status to DOWNLOADING.

    Cache folder binding happens asynchronously in step_task() on subsequent
    UI cycles, so we never block the UI here.
    """
    status_md, log_link = launch_mrjet(url)
    update_task(queue, url,
                Status=status_md,
                Log=log_link,
                LastProgressTime=time.time(),
                LastProgressValue=0.0,
                CacheFolder=None)

    save_queue(queue)


# ---------------------------------------------------------------------------
# Button handlers
# ---------------------------------------------------------------------------

def _handle_add(queue: dict) -> None:
    """Process the "Add" button: parse input, check duplicates, insert tasks."""
    raw = st.session_state.url_input_val
    # Normalise separators
    for sep in (",", "\n"):
        raw = raw.replace(sep, " ")
    items = [item.strip() for item in raw.split(" ") if item.strip()]

    added = 0
    skipped = 0
    exists = 0
    existing_names: list[str] = []

    # Pre-load existing filenames for duplicate check
    existing_normalized: list[str] = []
    try:
        if os.path.isdir(DOWNLOAD_DIR):
            existing_normalized = [
                normalize_id(f)
                for f in os.listdir(DOWNLOAD_DIR)
                if os.path.isfile(os.path.join(DOWNLOAD_DIR, f))
            ]
    except OSError as e:
        st.error(f"Error accessing download directory {DOWNLOAD_DIR}: {e}")

    for user_input in items:
        # Check if file already exists on disk
        check_name = user_input.split("#")[0].strip("/").split("/")[-1]
        norm = normalize_id(check_name)
        if any(norm in f for f in existing_normalized):
            exists += 1
            existing_names.append(check_name)
            continue

        full_url, display_name = parse_display_name(user_input)

        if full_url not in queue:
            from app.queue_manager import create_task
            task = create_task(display_name, full_url)
            queue[full_url] = task
            added += 1
        else:
            skipped += 1

    if added:
        st.success(f"Successfully added {added} new item(s).")
    if skipped:
        st.warning(f"Skipped {skipped} item(s) already in queue.")
    if exists:
        st.error(
            f"Skipped {exists} item(s) that may already exist: "
            f"{', '.join(existing_names)}"
        )

    if added:
        save_queue(queue)
        st.rerun()


def _handle_start_next(queue: dict) -> None:
    """Start the next *Not Started* task (manual button press)."""
    if is_any_downloading(queue):
        st.warning("A task is already downloading. Please wait for it to finish.")
        return

    url = find_next_not_started(queue)
    if url is None:
        st.info("No queued tasks to start.")
        return

    task = queue[url]
    st.info(f"Starting task: {task['DisplayName']}")

    _start_task(queue, url)
    st.rerun()


def _handle_clean(queue: dict) -> None:
    """Remove finished tasks and delete associated log files."""
    urls = finished_task_urls(queue)
    for url in urls:
        task = queue[url]
        log_val = task.get("Log", "")
        if log_val and "Takeover" not in log_val:
            try:
                log_file = log_val.split("/static/")[1].split(")")[0]
                log_path = os.path.join(STATIC_DIR, log_file)
                if os.path.exists(log_path):
                    os.remove(log_path)
            except (IndexError, AttributeError, OSError):
                pass
    remove_tasks(queue, urls)
    save_queue(queue)
    st.rerun()


def _auto_start_next_if_idle(queue: dict) -> None:
    """
    If no tasks are active and there is a *Not Started* task, launch it
    automatically (same core logic as the manual button).
    """
    if is_any_downloading(queue):
        return

    url = find_next_not_started(queue)
    if url is None:
        return

    task = queue[url]
    st.info(f"Queue idle — auto-starting next task: {task['DisplayName']}")
    time.sleep(AUTO_START_NOTICE_DELAY)

    _start_task(queue, url)
    st.rerun()
