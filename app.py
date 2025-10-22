import streamlit as st
import os
import time
import pandas as pd
import google.generativeai as genai # Thư viện Google Gemini
from dotenv import load_dotenv
from io import StringIO, BytesIO # BytesIO để xử lý dữ liệu ảnh nhị phân
from PIL import Image

load_dotenv()

# --- Cấu hình Gemini API ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    st.error("GOOGLE_API_KEY không được tìm thấy trong file .env. Vui lòng thêm API Key của bạn.")
    st.stop()

genai.configure(api_key=GOOGLE_API_KEY)

# --- THAY ĐỔI QUAN TRỌNG Ở ĐÂY: SỬ DỤNG CÁC MODEL ỔN ĐỊNH VÀ TƯƠNG THÍCH RỘNG ---
try:
    text_model = genai.GenerativeModel('gemini-flash-latest')
    vision_model = genai.GenerativeModel('gemini-flash-latest')
except Exception as e:
    st.error(f"Không thể khởi tạo model Gemini. Lỗi: {e}")
    st.stop()


# --- Hàm tương tác với Gemini API ---
def get_gemini_response(user_message, image_bytes=None, dataframe=None):
    """
    Hàm này gọi đến Google Gemini API để tạo phản hồi.
    """
    try:
        # --- Ưu tiên 1: Trả lời câu hỏi về ảnh nếu có ---
        if image_bytes:
            image = Image.open(BytesIO(image_bytes))
            if not user_message: # Nếu user_message rỗng khi chỉ tải ảnh
                user_message = "Mô tả chi tiết bức ảnh này."
            contents = [user_message, image]
            # Gọi đến model vision
            response = vision_model.generate_content(contents)
            return response.text

        # --- Ưu tiên 2: Trả lời câu hỏi về dữ liệu CSV nếu có ---
        if dataframe is not None:
            df_info_summary = f"Dữ liệu CSV có các cột: {', '.join(dataframe.columns.tolist())}. Một vài dòng đầu:\n{dataframe.head().to_markdown()}"
            prompt_for_gemini = f"Người dùng đã tải một file CSV. Dưới đây là thông tin về dữ liệu:\n\n{df_info_summary}\n\nHãy hành xử như một chuyên gia phân tích dữ liệu.\n\nCâu hỏi của người dùng là: '{user_message}'\n\nHãy trả lời câu hỏi này dựa trên thông tin được cung cấp."
            # Gọi đến model text
            response = text_model.generate_content(prompt_for_gemini)
            return response.text

        # --- Logic chat văn bản thuần túy ---
        # Gọi đến model text
        response = text_model.generate_content(user_message)
        return response.text
        
    except Exception as e:
        # Tách lỗi để hiển thị thông báo thân thiện hơn
        if "API key not valid" in str(e):
            return "Lỗi: API Key không hợp lệ. Vui lòng kiểm tra lại file .env của bạn."
        return f"Xin lỗi, tôi gặp sự cố khi tạo phản hồi. Lỗi: {e}"


# --- Cấu hình trang ---
st.set_page_config(
    page_title="Smart Chat App",
    page_icon="🤖",
    layout="wide"
)

# --- Quản lý Trạng thái Phiên (Session State) ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "uploaded_image" not in st.session_state:
    st.session_state.uploaded_image = None
if "dataframe" not in st.session_state:
    st.session_state.dataframe = None
if "dataframe_name" not in st.session_state:
    st.session_state.dataframe_name = ""


# --- Giao diện người dùng (UI) ---
st.title("🤖 Chat App Đa Năng")
st.write("Trò chuyện, phân tích ảnh và dữ liệu CSV.")

# --- Cấu trúc layout 2 cột ---
col1, col2 = st.columns([1, 2])

# --- CỘT 1: BẢNG ĐIỀU KHIỂN ---
with col1:
    st.header("Bảng điều khiển")

    with st.expander("🖼️ Chat với Ảnh", expanded=True):
        new_uploaded_image_file = st.file_uploader(
            "Tải lên một hình ảnh", type=["png", "jpg", "jpeg"]
        )
        if new_uploaded_image_file is not None:
            image_bytes = new_uploaded_image_file.getvalue()
            if st.session_state.uploaded_image is None or image_bytes != st.session_state.uploaded_image:
                st.session_state.uploaded_image = image_bytes
                st.session_state.messages.append({
                    "role": "system_info",
                    "content": "Một hình ảnh đã được tải lên và sẵn sàng để hỏi đáp:",
                    "image": image_bytes
                })
                st.rerun()
        
        # Thêm nút xóa ảnh để người dùng dễ dàng bắt đầu lại
        if st.session_state.uploaded_image:
            st.image(st.session_state.uploaded_image, caption="Ảnh đang được phân tích")
            if st.button("Xóa ảnh và bắt đầu lại"):
                st.session_state.uploaded_image = None
                st.session_state.messages.append({
                    "role": "system_info",
                    "content": "Ảnh đã được xóa. Bạn có thể tải lên ảnh mới."
                })
                st.rerun()


    with st.expander("📊 Chat với Dữ liệu CSV", expanded=True):
        uploaded_csv_file = st.file_uploader("Tải lên file CSV", type="csv", key="csv_upload")
        csv_url = st.text_input("Hoặc dán URL đến file CSV", key="csv_url_input")
        if st.button("Xử lý CSV", key="process_csv_button"):
            with st.spinner("Đang đọc và phân tích CSV..."):
                try:
                    df = None
                    file_source_name = ""
                    if uploaded_csv_file:
                        df = pd.read_csv(uploaded_csv_file)
                        file_source_name = uploaded_csv_file.name
                    elif csv_url:
                        df = pd.read_csv(csv_url)
                        file_source_name = csv_url.split('/')[-1]
                    else:
                        st.warning("Vui lòng tải file hoặc cung cấp URL.")
                        st.stop()
                    
                    st.session_state.dataframe = df
                    st.session_state.dataframe_name = file_source_name
                    st.session_state.messages.append({
                        "role": "system_info",
                        "content": f"Đã tải thành công file CSV '{st.session_state.dataframe_name}' với {df.shape[0]} dòng và {df.shape[1]} cột. Bạn có thể bắt đầu hỏi về dữ liệu này."
                    })
                    st.rerun()
                except Exception as e:
                    st.error(f"Đã xảy ra lỗi khi đọc CSV: {e}")
                    st.session_state.dataframe = None
                    st.session_state.dataframe_name = ""

# --- CỘT 2: KHUNG CHAT CHÍNH ---
with col2:
    for message in st.session_state.messages:
        role = message["role"]
        display_role = "assistant" if role == "system_info" else role
        with st.chat_message(display_role):
            if "image" in message:
                st.image(message["image"], width=200)
            if "content" in message:
                st.markdown(message["content"])

    if prompt := st.chat_input("Nhập câu hỏi của bạn..."):
        user_message_entry = {"role": "user", "content": prompt}
        if st.session_state.uploaded_image:
            user_message_entry["image"] = st.session_state.uploaded_image
        st.session_state.messages.append(user_message_entry)
        
        with st.chat_message("user"):
            if "image" in user_message_entry:
                st.image(user_message_entry["image"], width=200)
            st.markdown(user_message_entry["content"])

        with st.chat_message("assistant"):
            with st.spinner("AI đang suy nghĩ... 🤔"):
                response_content = get_gemini_response(
                    prompt, 
                    st.session_state.uploaded_image, 
                    st.session_state.dataframe
                )
                st.markdown(response_content)
        
        st.session_state.messages.append({"role": "assistant", "content": response_content})
        # Sau khi AI đã trả lời câu hỏi về ảnh, xóa nó đi để các câu hỏi sau không bị ảnh hưởng
        if st.session_state.uploaded_image:
            st.session_state.uploaded_image = None