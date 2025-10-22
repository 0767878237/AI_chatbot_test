import streamlit as st
import os
import time
import pandas as pd
from dotenv import load_dotenv
from io import StringIO
from PIL import Image

load_dotenv()

# --- Cấu hình trang ---
st.set_page_config(
    page_title="Smart Chat App",
    page_icon="🤖",
    layout="wide"
)

# --- Model AI Giả lập (Mock AI Model) ---
def get_mock_ai_response(user_message, image_bytes=None, dataframe=None):
    """
    Hàm giả lập AI, giờ đây có thể "đọc" được DataFrame từ CSV và ảnh.
    """
    user_message = user_message.lower()

    # --- Ưu tiên 1: Trả lời câu hỏi về dữ liệu CSV nếu có ---
    if dataframe is not None:
        if "tóm tắt" in user_message or "summarize" in user_message:
            buffer = StringIO()
            dataframe.info(buf=buffer)
            summary = buffer.getvalue()
            return f"Đây là tóm tắt bộ dữ liệu của bạn:\n\n```\n{summary}\n```"
        
        elif "thống kê" in user_message or "stats" in user_message:
            stats = dataframe.describe().to_markdown()
            return f"Đây là các thống kê cơ bản cho các cột số:\n\n{stats}"

        elif "thiếu" in user_message or "missing" in user_message:
            missing_values = dataframe.isnull().sum()
            most_missing = missing_values.sort_values(ascending=False).to_markdown()
            return f"Đây là số lượng giá trị bị thiếu trong mỗi cột:\n\n{most_missing}"
        
        else:
            return "Tôi đã sẵn sàng nhận câu hỏi về file CSV. Bạn muốn biết gì về dữ liệu này?"


    # --- Ưu tiên 2: Trả lời câu hỏi về ảnh nếu có ---
    if image_bytes:
        if "what is in this photo" in user_message or "có gì trong ảnh" in user_message:
            return "Đây là một câu trả lời giả lập: Bức ảnh bạn gửi có vẻ như chứa..."
        elif "màu gì" in user_message: # Thêm logic ví dụ cho ảnh
            return "Đây là một câu trả lời giả lập: Màu sắc chủ đạo trong ảnh là..."
        else:
            return f"Đây là một câu trả lời giả lập: Tôi đã nhận được ảnh và câu hỏi của bạn: '{user_message}'."

    # --- Logic chat thông thường ---
    if "xin chào" in user_message:
        return "Xin chào! Tôi có thể giúp gì cho bạn hôm nay?"
    elif "bạn tên là gì" in user_message:
        return "Tôi là một trợ lý AI được tạo ra để demo."
    else:
        return f"Tôi đã nhận được tin nhắn của bạn: '{user_message}'. Đây là một câu trả lời mẫu."


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
st.title("Chat App Đa Năng")
st.write("Trò chuyện, phân tích ảnh và dữ liệu CSV.")

# --- Cấu trúc layout 2 cột ---
col1, col2 = st.columns([1, 2])

# --- CỘT 1: SIDEBAR TẢI FILE ---
with col1:
    st.header("Bảng điều khiển")

    # --- Xử lý Ảnh ---
    with st.expander("Chat với Ảnh", expanded=True):
        new_uploaded_image_file = st.file_uploader(
            "Tải lên một hình ảnh", type=["png", "jpg", "jpeg"]
        )
        
        # Nếu có file ảnh mới được tải lên VÀ nó khác với ảnh hiện có trong session state
        if new_uploaded_image_file is not None and (
            st.session_state.uploaded_image is None or 
            new_uploaded_image_file.getvalue() != st.session_state.uploaded_image
        ):
            image_bytes = new_uploaded_image_file.getvalue()
            st.session_state.uploaded_image = image_bytes
            
            # Thêm thông báo và ảnh vào lịch sử chat NGAY LẬP TỨC
            st.session_state.messages.append({
                "role": "system_info", # Vai trò đặc biệt cho thông báo hệ thống
                "content": "Một hình ảnh đã được tải lên và sẵn sàng để hỏi đáp:",
                "image": image_bytes
            })
            # Tự động scroll xuống cuối chat
            st.rerun() # Yêu cầu Streamlit chạy lại để hiển thị cập nhật ngay


    # --- Xử lý CSV ---
    with st.expander("Chat với Dữ liệu CSV", expanded=True):
        uploaded_csv_file = st.file_uploader(
            "Tải lên file CSV", type="csv", key="csv_upload" # Thêm key để phân biệt
        )
        csv_url = st.text_input("Hoặc dán URL đến file CSV", key="csv_url_input")

        # Nút xử lý
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
                    
                    # Thêm thông báo vào lịch sử chat
                    st.session_state.messages.append({
                        "role": "system_info",
                        "content": f"Đã tải thành công file CSV '{st.session_state.dataframe_name}' với {df.shape[0]} dòng và {df.shape[1]} cột. Bạn có thể bắt đầu hỏi về dữ liệu này."
                    })
                    st.rerun() # Chạy lại để hiển thị thông báo ngay lập tức

                except Exception as e:
                    st.error(f"Đã xảy ra lỗi khi đọc CSV: {e}")
                    st.session_state.dataframe = None
                    st.session_state.dataframe_name = ""


# --- CỘT 2: KHUNG CHAT CHÍNH ---
with col2:
    # Hiển thị các tin nhắn đã có trong lịch sử
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if "image" in message:
                st.image(message["image"], width=200)
            # if "dataframe" in message: # Không hiển thị dataframe trực tiếp trong chat
            #     st.dataframe(message["dataframe"])
            if "content" in message:
                st.markdown(message["content"])

    # Ô nhập liệu và nút gửi
    if prompt := st.chat_input("Nhập câu hỏi của bạn..."):
        user_message_entry = {"role": "user", "content": prompt}
        # Nếu có ảnh đang chờ xử lý, đính kèm nó vào tin nhắn của user
        if st.session_state.uploaded_image:
            user_message_entry["image"] = st.session_state.uploaded_image
        
        st.session_state.messages.append(user_message_entry)
        
        with st.chat_message("user"):
            if "image" in user_message_entry:
                st.image(user_message_entry["image"], width=200)
            st.markdown(user_message_entry["content"])

        # Tạo phản hồi từ AI
        with st.chat_message("assistant"):
            with st.spinner("AI đang suy nghĩ... "):
                response_content = get_mock_ai_response(
                    prompt, 
                    st.session_state.uploaded_image, 
                    st.session_state.dataframe
                )
                time.sleep(1)
                st.markdown(response_content)
        
        st.session_state.messages.append({"role": "assistant", "content": response_content})

        # Xóa ảnh đã xử lý khỏi state sau khi AI đã dùng nó để trả lời
        # để nó không bị gửi ở các lượt sau
        st.session_state.uploaded_image = None