"""app.py"""
import os
import json
from io import BytesIO
import streamlit as st
import pandas as pd
import google.generativeai as genai
import matplotlib.pyplot as plt
from dotenv import load_dotenv
from PIL import Image

# Tải các biến môi trường từ file .env
load_dotenv()

# --- Cấu hình trang Streamlit ---
st.set_page_config(
    page_title="Smart Chat App",
    page_icon="🤖",
    layout="wide"
)

# --- Gemini API ---
def configure_gemini():
    """Model Gemini."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        st.error("GOOGLE_API_KEY not found")
        st.stop()

    genai.configure(api_key=api_key)
    try:
        model = genai.GenerativeModel('gemini-flash-latest')
        return model
    except Exception as e:
        st.error(f"Cannot initialize Gemini model. Error: {e}")
        st.stop()

model = configure_gemini()

# --- Session State Management ---
def initialize_session_state():
    """Initialize necessary values in session state."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "uploaded_image" not in st.session_state:
        st.session_state.uploaded_image = None
    if "dataframe" not in st.session_state:
        st.session_state.dataframe = None
    if "dataframe_name" not in st.session_state:
        st.session_state.dataframe_name = ""

initialize_session_state()

# --- CREATE PLOT ---
def create_plot(plot_info):
    """
    Create a plot using Matplotlib based on information from AI.
    Returns a BytesIO object containing the image of the plot.
    """
    df = st.session_state.dataframe
    if df is None:
        return None

    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots()
    plot_type = plot_info.get("type")

    try:
        if plot_type == "histogram":
            column = plot_info.get("column")
            if column in df.columns:
                ax.hist(df[column].dropna(), bins=20, edgecolor='black')
                ax.set_title(f"Distribution of column '{column}'")
                ax.set_xlabel(column)
                ax.set_ylabel("Frequency")
            else:
                return f"Error: Column '{column}' not found."

        elif plot_type == "bar":
            x_col = plot_info.get("x_column")
            y_col = plot_info.get("y_column")
            if x_col in df.columns and y_col in df.columns:
                top_data = df.nlargest(15, y_col).sort_values(y_col, ascending=False)
                ax.bar(top_data[x_col], top_data[y_col])
                ax.set_title(f"Bar chart comparing '{x_col}' and '{y_col}'")
                ax.set_xlabel(x_col)
                ax.set_ylabel(y_col)
                plt.xticks(rotation=45, ha="right")
            else:
                return f"Error: Column '{x_col}' or '{y_col}' not found."

        else:
            return f"Error: Plot type '{plot_type}' not supported."

        plt.tight_layout()
        buf = BytesIO()
        fig.savefig(buf, format="png")
        buf.seek(0)
        plt.close(fig)
        return buf

    except Exception as e:
        plt.close(fig)
        return f"Error occurred while creating plot: {e}"

# --- Interaction with Gemini API ---
def get_gemini_response_stream(user_message, image_bytes=None, dataframe=None):
    """
    This function calls the Google Gemini API and returns a generator to stream the response.
    """
    try:
        contents = []
        prompt = user_message

        # --- CSV PROMPT ---
        if dataframe is not None:
            df_info_summary = f"CSV data has columns: {', '.join(dataframe.columns.tolist())}."

            # Instructions for AI on how to request a plot
            plotting_instruction = (
                "IMPORTANT: If the user requests a plot (plot, chart, graph, draw), "
                "you MUST respond with a single JSON string, without any explanations or markdown formatting.\n"
                "Supported JSON formats are:\n"
                "1. Histogram: {\"plot\": {\"type\": \"histogram\", \"column\": \"column_name\"}}\n"
                "2. Bar chart: {\"plot\": {\"type\": \"bar\", \"x_column\": \"x_column_name\", \"y_column\": \"y_column_name\"}}\n"
                "If not, answer the user's question as a data analysis expert."
            )

            prompt = (
                f"{plotting_instruction}\n\n"
                f"Data info: {df_info_summary}\n"
                f"User question: '{user_message}'"
            )

        # ... (img handling) ...
        if image_bytes:
            image = Image.open(BytesIO(image_bytes))
            if not prompt:
                prompt = "Description image details."
            contents = [prompt, image]
        else:
            contents = [prompt]

        response_stream = model.generate_content(contents, stream=True)

        for chunk in response_stream:
            if chunk.parts:
                yield chunk.text

    except Exception as e:
        yield f"Error occurred while creating response: {e}"


# --- User Interface (UI) ---
st.title("🤖 Multi-Purpose Chat App")
st.write("Chat, analyze images and CSV data with the power of Google Gemini.")

col1, col2 = st.columns([1, 2])

with col1:
    st.header("Dashboard")
    if st.button("🗑️ Clear Chat"):
        # ... (logic delete button) ...
        st.session_state.messages, st.session_state.uploaded_image, st.session_state.dataframe, st.session_state.dataframe_name = [], None, None, ""
        st.rerun()

    with st.expander("🖼️ Image", expanded=True):
        # ... (logic image) ...
        uploaded_image_file = st.file_uploader(
            "Upload an image",
            type=["png", "jpg", "jpeg"],
            label_visibility="collapsed"
        )
        if uploaded_image_file:
            image_bytes = uploaded_image_file.getvalue()
            if st.session_state.uploaded_image != image_bytes:
                st.session_state.uploaded_image = image_bytes
                st.session_state.messages.append({
                    "role": "system_info",
                    "content": "An image has been uploaded.",
                    "image": image_bytes
                })
                st.rerun()
        if st.session_state.uploaded_image:
            st.image(st.session_state.uploaded_image, caption="Image being analyzed")

    with st.expander("📊 Chat with CSV Data", expanded=True):
        # ... (logic upload CSV) ...
        if st.session_state.dataframe_name:
            st.info(f"Chatting with: {st.session_state.dataframe_name}")
            if st.button("Delete CSV Data"):
                st.session_state.dataframe, st.session_state.dataframe_name = None, ""
                st.session_state.messages.append({
                    "role": "system_info", 
                    "content": "CSV data has been deleted."
                    })
                st.rerun()
        uploaded_csv_file = st.file_uploader("Upload CSV file", type="csv", key="csv_upload")
        csv_url = st.text_input("Or paste URL to CSV file", key="csv_url_input")
        if st.button("Process CSV", key="process_csv_button"):
            with st.spinner("Reading and analyzing CSV..."):
                try:
                    df, file_name = (
                        pd.read_csv(uploaded_csv_file), 
                        uploaded_csv_file.name) if uploaded_csv_file else (
                            pd.read_csv(csv_url), csv_url.split('/')[-1]) if csv_url else (None, "")
                    if df is not None:
                        st.session_state.dataframe, st.session_state.dataframe_name = df, file_name
                        st.session_state.messages.append({
                            "role": "system_info",
                            "content": f"Successfully uploaded file '{file_name}' with {df.shape[0]} rows and {df.shape[1]} columns."
                            })
                        st.rerun()
                    else: st.warning("Upload file or URL.")
                except Exception as e: st.error(f"Error reading CSV: {e}")

with col2:
    chat_container = st.container(height=600)
    with chat_container:
        for message in st.session_state.messages:
            role = message["role"]
            AVATAR = "ℹ️" if role == "system_info" else "👤" if role == "user" else "🤖"
            with st.chat_message(role, avatar=AVATAR):
                if "image" in message:
                    st.image(message["image"], width=200)
                if "content" in message:
                    st.markdown(message["content"])

    if prompt := st.chat_input("Enter your question..."):
        user_message_entry = {"role": "user", "content": prompt}
        if st.session_state.uploaded_image: user_message_entry["image"] = st.session_state.uploaded_image
        st.session_state.messages.append(user_message_entry)

        with chat_container:
             with st.chat_message("user", avatar="👤"):
                if "image" in user_message_entry: st.image(user_message_entry["image"], width=200)
                st.markdown(user_message_entry["content"])

        # --- LOGIC RESPONSE ---
        with chat_container:
            with st.chat_message("assistant", avatar="🤖"):
                with st.spinner("AI is thinking... 🤔"):
                    response_generator = get_gemini_response_stream(
                        prompt, st.session_state.uploaded_image, st.session_state.dataframe
                    )
                    # Combine the chunks into a complete response.
                    FULL_RESPONSE = "".join([chunk for chunk in response_generator])

                # CHECK IF THE FEEDBACK IS A REQUEST FOR A GRAPHIC DRAWING OR NOT
                IS_PLOT_REQUEST = False
                try:
                    # Analyze the JSON string
                    json_response = json.loads(FULL_RESPONSE)
                    if "plot" in json_response:
                        IS_PLOT_REQUEST = True
                        with st.spinner("Creating plot... 🎨"):
                            plot_image_buffer = create_plot(json_response["plot"])
                            if isinstance(plot_image_buffer, BytesIO):
                                st.image(plot_image_buffer, caption="Plot created by AI")
                                st.session_state.messages.append(
                                    {"role": "assistant",
                                    "image": plot_image_buffer,
                                    "content": "Here is the plot you requested:"})
                            else: # If the create_plot function returns an error string
                                st.error(plot_image_buffer)
                                st.session_state.messages.append(
                                    {"role": "assistant", "content": plot_image_buffer})
                except json.JSONDecodeError:
                    # If it's not JSON, then it's regular text
                    IS_PLOT_REQUEST = False

                # If there is no request to draw a graph, display the text as usual
                if not IS_PLOT_REQUEST:
                    st.markdown(FULL_RESPONSE)
                    st.session_state.messages.append({"role": "assistant","content": FULL_RESPONSE})

        st.session_state.uploaded_image = None
