import subprocess
import time
import streamlit as st
import pandas as pd
import os
import uuid

st.set_page_config(
    page_title="Miyuki WebGUI",
    page_icon="random",
    layout="centered",
    initial_sidebar_state="auto",
)

if "download_queue" not in st.session_state:
    st.session_state.download_queue = {}

test_params = ["-ffmpeg", "-quality", "360", "-urls"]
prod_params = ["-ffmpeg", "-urls"]

# create a temp dir
static_dir = os.path.join(os.getcwd(), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

def download_file(video_url_input):
    movie_id = video_url_input.split("/")[-1]
    command = " ".join(["miyuki", " ".join(prod_params), video_url_input])
    process = subprocess.Popen(f"{command}",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        shell=True
    )
    stdout, stderr = process.communicate()
    log_id = uuid.uuid4()

    log_file_path = os.path.join(static_dir, f"{log_id}.log")
    with open(log_file_path, "w") as f:
        f.write(stderr)

    log_link = f"[logfile](./static/{log_id}.log)"

    if f"File integrity for {movie_id}: 100.00%" in stderr:
        return ":green-background[Success]", log_link
    else:
        return ":red-background[Failed]", log_link

st.title("Miyuki WebGUI")

input_col , add_col, start_col = st.columns((5,1,1))

queue_data = pd.DataFrame(columns=["URL", "Created Date", "Status", "Log"], data=st.session_state.download_queue.values())

table_placeholder = st.empty() 
table_placeholder.table(queue_data)

with input_col:
    url_input = st.text_input("v", label_visibility="collapsed", placeholder="Enter a URL")
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
            "Log": ""
        }
        queue_data = pd.DataFrame(columns=["URL", "Created Date", "Status", "Log"], data=st.session_state.download_queue.values())
        table_placeholder.table(queue_data)
    else:
        st.warning("This URL is already in the download queue.")

if start_button:
    for url, task in st.session_state.download_queue.items():

        if task["Status"] == ":gray-background[Not Started]":
            st.session_state.download_queue[url]["Status"] = ":orange-background[Downloading]"
            table_placeholder.table(pd.DataFrame(st.session_state.download_queue.values()))

            result = download_file(url)
            st.session_state.download_queue[url]["Status"] = result[0]
            st.session_state.download_queue[url]["Log"] = result[1]
            table_placeholder.table(pd.DataFrame(st.session_state.download_queue.values()))


with st.expander("Utils", expanded=False, icon=None):
    clean_log = st.button("Clean log")
    if clean_log:
        subprocess.Popen(f"rm -rf {static_dir}/*.log", shell=True)
        subprocess.Popen("rm ffmpeg_input_miyuki.txt", shell=True)
        subprocess.Popen("rm miyuki.log", shell=True)
        subprocess.Popen("rm tmp_movie_miyuki.html", shell=True)
        subprocess.Popen("rm downloaded_urls_miyuki.txt", shell=True)
