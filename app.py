import streamlit as st
import boto3
import json
import base64
from PIL import Image
import os
from datetime import datetime
import hashlib

# -----------------------
# SETUP
# -----------------------

client = boto3.client("bedrock-runtime")

os.makedirs("gallery", exist_ok=True)
os.makedirs("history", exist_ok=True)

st.title("AI Marketing Content Studio")

# -----------------------
# USER SESSION
# -----------------------

st.sidebar.header("User Session")

user = st.sidebar.selectbox(
    "Select user",
    ["Designer_1", "Writer_2", "Approver_3"]
)

roles = {
    "Designer_1": "designer",
    "Writer_2": "writer",
    "Approver_3": "approver"
}

role = roles[user]

st.sidebar.write("Current user:", user)
st.sidebar.write("Role:", role)

# -----------------------
# ETHICAL POLICY
# -----------------------

# -----------------------
# TABS
# -----------------------

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["Image Generator", "Text Editor", "Gallery", "History", "Comments"]
)

# -----------------------
# CONTENT MODERATION
# -----------------------

banned_words = ["violence", "hate", "weapon"]

def moderate(text):
    return any(word in text.lower() for word in banned_words)

# -----------------------
# SIMPLE ENCRYPTION
# -----------------------

def encrypt_content(text):
    return hashlib.sha256(text.encode()).hexdigest()

# -----------------------
# IMAGE GENERATION
# -----------------------

with tab1:

    st.header("Generate Images")

    prompt = st.text_area("Describe the image")

    style = st.selectbox(
        "Style",
        ["Realistic", "Anime", "Oil Painting", "Digital Art"]
    )

    if role != "designer":
        st.info("Only designers can generate images")

    if role == "designer":

        if st.button("Generate Image"):

            if moderate(prompt):
                st.error("Prompt violates ethical policy")
                st.stop()

            full_prompt = f"{prompt} style {style}"

            body = {
                "taskType": "TEXT_IMAGE",
                "textToImageParams": {
                    "text": full_prompt
                },
                "imageGenerationConfig": {
                    "numberOfImages": 1,
                    "height": 512,
                    "width": 512
                }
            }

            response = client.invoke_model(
                modelId="amazon.titan-image-generator-v2:0",
                body=json.dumps(body)
            )

            result = json.loads(response["body"].read())

            image_base64 = result["images"][0]

            image_bytes = base64.b64decode(image_base64)

            filename = f"gallery/{datetime.now().timestamp()}.png"

            with open(filename, "wb") as f:
                f.write(image_bytes)

            st.image(image_bytes)

            st.success("Image saved to gallery")

# -----------------------
# TEXT EDITOR
# -----------------------

with tab2:

    st.header("AI Text Editor")

    text = st.text_area(
        "Write or paste text",
        value=st.session_state.get("reverted_text", "")
    )

    action = st.selectbox(
        "Select action",
        ["Summarize", "Expand", "Correct Grammar", "Generate Variations"]
    )

    if role != "writer":
        st.info("Only writers can edit text")

    if role == "writer":

        if st.button("Process Text"):

            if moderate(text):
                st.error("Content violates ethical policy")
                st.stop()

            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 300,
                "messages": [
                    {
                        "role": "user",
                        "content": f"{action} the following text:\n{text}"
                    }
                ]
            }

            response = client.invoke_model(
                modelId="anthropic.claude-3-haiku-20240307-v1:0",
                body=json.dumps(body)
            )

            result = json.loads(response["body"].read())

            output = result["content"][0]["text"]

            st.subheader("Result")

            st.write(output)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            filename = f"history/{timestamp}.txt"

            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"ACTION: {action}\n\n")
                f.write(f"ORIGINAL:\n{text}\n\n")
                f.write(f"RESULT:\n{output}\n\n")
                f.write(f"HASH:{encrypt_content(output)}")

# -----------------------
# GALLERY
# -----------------------

with tab3:

    st.header("Generated Images")

    images = os.listdir("gallery")

    if len(images) == 0:

        st.write("No images generated yet")

    else:

        for img in images:

            path = f"gallery/{img}"

            image = Image.open(path)

            st.image(image)

# -----------------------
# HISTORY
# -----------------------

with tab4:

    st.header("Text History")

    files = sorted(os.listdir("history"), reverse=True)

    if len(files) == 0:

        st.write("No history yet")

    else:

        selected_file = st.selectbox("Select version", files)

        path = f"history/{selected_file}"

        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        st.text_area(
            "Saved Version",
            content,
            height=300,
            key="history_view"
        )

        # -----------------------
        # COMPARE VERSIONS
        # -----------------------

        st.subheader("Compare Versions")

        file1 = st.selectbox("Version 1", files, key="v1")
        file2 = st.selectbox("Version 2", files, key="v2")

        if file1 and file2:

            with open(f"history/{file1}", "r", encoding="utf-8", errors="ignore") as f:
                text1 = f.read()

            with open(f"history/{file2}", "r", encoding="utf-8", errors="ignore") as f:
                text2 = f.read()

            col1, col2 = st.columns(2)

            with col1:

                st.text_area(
                    "Version 1",
                    text1,
                    height=300,
                    key="compare1"
                )

            with col2:

                st.text_area(
                    "Version 2",
                    text2,
                    height=300,
                    key="compare2"
                )

        # -----------------------
        # REVERT VERSION
        # -----------------------

        st.subheader("Revert Version")

        if st.button("Load this version into editor"):

            st.session_state["reverted_text"] = content

            st.success("Version loaded into editor")

        # -----------------------
        # APPROVAL WORKFLOW
        # -----------------------

        st.subheader("Approval Workflow")

        if role == "approver":

            if st.button("Approve this version"):

                approved = f"approved_{selected_file}"

                os.rename(
                    f"history/{selected_file}",
                    f"history/{approved}"
                )

                st.success("Content approved")

        else:

            st.info("Only approvers can approve content")
with tab5:
        # -----------------------
        # COMMENTS
        # -----------------------

        st.subheader("Comments")

        comment = st.text_area("Add comment")

        if st.button("Save Comment"):

            comment_file = f"history/{selected_file}_comments.txt"

            with open(comment_file, "a", encoding="utf-8") as f:

                f.write(f"{user}: {comment}\n")

            st.success("Comment saved")

        comment_file = f"history/{selected_file}_comments.txt"

        if os.path.exists(comment_file):

            st.write("Previous comments")

            with open(comment_file, "r", encoding="utf-8", errors="ignore") as f:

                st.text(f.read())