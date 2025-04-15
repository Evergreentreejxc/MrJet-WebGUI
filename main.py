import subprocess
import time
import streamlit as st
import pandas as pd
import os
import uuid
import json

st.set_page_config(
    page_title="MrJet WebGUI",
    page_icon="random",
    layout="centered",
    initial_sidebar_state="auto",
)


static_dir = os.path.join(os.getcwd(), "static")
queue_file = os.path.join(os.getcwd(), "download_queue.json")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)


def load_queue():
    if os.path.exists(queue_file):
        with open(queue_file, "r") as f:
            return json.load(f)
    return {}


def save_queue(queue):
    with open(queue_file, "w") as f:
        json.dump(queue, f)


if "download_queue" not in st.session_state:
    st.session_state.download_queue = load_queue()


def download_file(video_url_input):
    movie_id = video_url_input.split("/")[-1]
    log_id = uuid.uuid4()
    log_file_path = os.path.join(static_dir, f"{log_id}.log")

    command = " ".join(
        ["mrjet", "--url", video_url_input, "--output_dir", "mrjet_output"]
    )

    with open(log_file_path, "w") as log_file:
        subprocess.Popen(
            command, stdout=log_file, stderr=log_file, text=True, shell=True
        )

    log_link = f"[logfile](./app/static/{log_id}.log)"
    return ":orange-background[Downloading]", log_link


def check_task_status(url, log_link):
    if not log_link:
        return ":gray-background[Not Started]", ""

    log_file = log_link.split("/static/")[1].split(")")[0]
    log_path = os.path.join(static_dir, log_file)
    if os.path.exists(log_path):
        with open(log_path, "r") as f:
            content = f.read()
            movie_id = url.split("/")[-1]
            if f"100%" in content:
                return ":green-background[Success]", log_link
            elif "Error" in content:
                return ":red-background[Failed]", log_link
    return ":orange-background[Downloading]", log_link


st.title("MrJet WebGUI")

input_col, add_col, start_col = st.columns((5, 1, 1))

for url in list(st.session_state.download_queue.keys()):
    if st.session_state.download_queue[url]["Status"] in [
        ":gray-background[Not Started]",
        ":orange-background[Downloading]",
        ":red-background[Failed]",
    ]:
        status, log = check_task_status(
            url, st.session_state.download_queue[url]["Log"]
        )
        st.session_state.download_queue[url]["Status"] = status
        st.session_state.download_queue[url]["Log"] = log

save_queue(st.session_state.download_queue)

queue_data = pd.DataFrame(
    columns=["URL", "Created Date", "Status", "Log"],
    data=st.session_state.download_queue.values(),
)

table_placeholder = st.empty()
table_placeholder.table(queue_data)

with input_col:
    url_input = st.text_input(
        "v", label_visibility="collapsed", placeholder="Enter a URL"
    )
with add_col:
    add_button = st.button("Add", use_container_width=True)
with start_col:
    start_button = st.button("Start", use_container_width=True)


if add_button:
    if not url_input:
        st.error("Please enter a URL.")
    elif not url_input.startswith("http"):
        st.error("Please enter a valid URL starting with 'http' or 'https'.")
    elif url_input not in st.session_state.download_queue:
        video_id = url_input.split("/")[-1]
        st.session_state.download_queue[url_input] = {
            "URL": f"[{video_id}]({url_input})",
            "Created Date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "Status": ":gray-background[Not Started]",
            "Log": "",
        }
        save_queue(st.session_state.download_queue)
        queue_data = pd.DataFrame(
            columns=["URL", "Created Date", "Status", "Log"],
            data=st.session_state.download_queue.values(),
        )
        table_placeholder.table(queue_data)
    else:
        st.warning("This URL is already in the download queue.")

if start_button:
    for url, task in st.session_state.download_queue.items():
        if task["Status"] == ":gray-background[Not Started]":
            result = download_file(url)
            st.session_state.download_queue[url]["Status"] = result[0]
            st.session_state.download_queue[url]["Log"] = result[1]
            save_queue(st.session_state.download_queue)
            table_placeholder.table(
                pd.DataFrame(st.session_state.download_queue.values())
            )
        elif task["Status"] == ":orange-background[Downloading]":
            status, log = check_task_status(url, task["Log"])
            st.session_state.download_queue[url]["Status"] = status
            st.session_state.download_queue[url]["Log"] = log
            save_queue(st.session_state.download_queue)
            table_placeholder.table(
                pd.DataFrame(st.session_state.download_queue.values())
            )


with st.expander("Utils", expanded=False, icon=None):
    clean_log = st.button("Clean log")

    if clean_log:
        urls_to_remove = []
        for url, task in st.session_state.download_queue.items():
            if task["Status"] in [
                ":green-background[Success]",
                ":red-background[Failed]",
            ]:
                if task["Log"]:
                    log_file = task["Log"].split("/static/")[1].split(")")[0]
                    log_path = os.path.join(static_dir, log_file)
                    if os.path.exists(log_path):
                        os.remove(log_path)
                urls_to_remove.append(url)

        for url in urls_to_remove:
            del st.session_state.download_queue[url]

        # subprocess.Popen("rm miyuki.log", shell=True)

        save_queue(st.session_state.download_queue)
        table_placeholder.table(pd.DataFrame(st.session_state.download_queue.values()))
