import streamlit as st
import os
import time
from dotenv import load_dotenv
from PIL import Image

# Tải các biến môi trường
load_dotenv()

# --- Cấu hình trang ---
st.set_page_config(
    page_title="Gemini Chat App",
    page_icon="🤖",
    layout="centered"
)

# --- Model AI Giả lập (Mock AI Model) ---
def get_mock_ai_response(user_message, image_bytes=None):
    """
    Hàm giả lập AI, giờ đây có thể "nhìn" được ảnh.
    """
    user_message = user_message.lower()
    
    # Nếu có ảnh được gửi kèm
    if image_bytes:
        # Giả lập AI phân tích ảnh
        if "what is in this photo" in user_message or "có gì trong ảnh" in user_message:
            return "Đây là một câu trả lời giả lập: Bức ảnh bạn gửi có vẻ như chứa..."
        elif "màu gì" in user_message:
             return "Đây là một câu trả lời giả lập: Màu sắc chủ đạo trong ảnh là..."
        else:
            return f"Đây là một câu trả lời giả lập: Tôi đã nhận được ảnh và câu hỏi của bạn: '{user_message}'."
    
    # Logic cũ nếu không có ảnh
    if "xin chào" in user_message:
        return "Xin chào! Tôi có thể giúp gì cho bạn hôm nay?"
    elif "bạn tên là gì" in user_message:
        return "Tôi là một trợ lý AI được tạo ra để demo."
    else:
        return f"Tôi đã nhận được tin nhắn của bạn: '{user_message}'. Đây là một câu trả lời mẫu."

# --- Quản lý Trạng thái Phiên (Session State) ---
if "messages" not in st.session_state:
    st.session_state.messages = []
# Thêm state để lưu trữ file được tải lên
if "uploaded_image" not in st.session_state:
    st.session_state.uploaded_image = None


# --- Giao diện người dùng (UI) ---
st.title("🤖 Chat App Đa Năng")
st.write("Trò chuyện, phân tích ảnh và dữ liệu CSV.")
st.markdown("---")


# --- PHẦN UI MỚI: KHU VỰC TẢI FILE ---
with st.sidebar:
    st.header("Tải tệp lên")
    # Widget tải ảnh
    uploaded_file = st.file_uploader(
        "Tải lên một hình ảnh", type=["png", "jpg", "jpeg"], label_visibility="collapsed"
    )
    if uploaded_file:
        # Đọc dữ liệu ảnh và lưu vào session state
        image_bytes = uploaded_file.getvalue()
        st.session_state.uploaded_image = image_bytes
        # Hiển thị ảnh preview
        st.image(image_bytes, caption="Ảnh đã tải lên")


# Hiển thị các tin nhắn đã có trong lịch sử
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        # Xử lý hiển thị nội dung, có thể bao gồm cả ảnh
        if "image" in message:
            st.image(message["image"], width=200)
        if "content" in message:
            st.markdown(message["content"])

# Ô nhập liệu và nút gửi
if prompt := st.chat_input("Nhập câu hỏi của bạn..."):
    # Tạo một tin nhắn mới của người dùng để thêm vào lịch sử
    user_message = {"role": "user", "content": prompt}

    # Nếu có ảnh đang chờ xử lý, đính kèm nó vào tin nhắn
    if st.session_state.uploaded_image:
        user_message["image"] = st.session_state.uploaded_image
    
    # Thêm tin nhắn vào lịch sử và hiển thị
    st.session_state.messages.append(user_message)
    with st.chat_message("user"):
        if "image" in user_message:
            st.image(user_message["image"], width=200)
        st.markdown(user_message["content"])

    # Tạo phản hồi từ AI
    with st.chat_message("assistant"):
        with st.spinner("AI đang suy nghĩ... 🤔"):
            response_content = get_mock_ai_response(prompt, st.session_state.uploaded_image)
            time.sleep(1)
            st.markdown(response_content)
    
    # Thêm phản hồi của AI vào lịch sử
    st.session_state.messages.append({"role": "assistant", "content": response_content})

    # Quan trọng: Xóa ảnh đã xử lý khỏi state để nó không bị gửi ở các lượt sau
    st.session_state.uploaded_image = None