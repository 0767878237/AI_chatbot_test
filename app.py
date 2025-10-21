import streamlit as st
import os
import time
from dotenv import load_dotenv

# Tải các biến môi trường (dù không dùng API ở bước này, giữ lại là thói quen tốt)
load_dotenv()

# --- Cấu hình trang ---
st.set_page_config(
    page_title="Gemini Chat App",
    page_icon="🤖",
    layout="centered"
)

# --- Model AI Giả lập (Mock AI Model) ---
def get_mock_ai_response(user_message):
    """
    Hàm này giả lập việc gọi đến một model AI.
    Nó sẽ trả về một câu trả lời được lập trình sẵn dựa trên tin nhắn người dùng.
    """
    # Chuyển tin nhắn về chữ thường để dễ so sánh
    user_message = user_message.lower()
    
    if "xin chào" in user_message:
        return "Xin chào! Tôi có thể giúp gì cho bạn hôm nay?"
    elif "bạn tên là gì" in user_message:
        return "Tôi là một trợ lý AI được tạo ra để demo."
    elif "khỏe không" in user_message:
        return "Tôi khỏe, cảm ơn bạn đã hỏi! Còn bạn thì sao?"
    else:
        return f"Tôi đã nhận được tin nhắn của bạn: '{user_message}'. Đây là một câu trả lời mẫu."

# --- Quản lý Trạng thái Phiên (Session State) ---
# Khởi tạo lịch sử chat nếu nó chưa tồn tại
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Giao diện người dùng (UI) ---
st.title("🤖 Chat App Đa Năng")
st.write("Trò chuyện, phân tích ảnh và dữ liệu CSV.")
st.markdown("---")

# Hiển thị các tin nhắn đã có trong lịch sử
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Ô nhập liệu và nút gửi
if prompt := st.chat_input("Nhập câu hỏi của bạn..."):
    # 1. Thêm tin nhắn của người dùng vào lịch sử và hiển thị
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Tạo phản hồi từ AI và hiển thị
    with st.chat_message("assistant"):
        # Hiển thị chỉ báo đang tải (loading spinner)
        with st.spinner("AI đang suy nghĩ... 🤔"):
            # Gọi model AI giả lập
            response = get_mock_ai_response(prompt)
            # Giả lập thời gian xử lý
            time.sleep(1) 
            st.markdown(response)
    
    # 3. Thêm phản hồi của AI vào lịch sử
    st.session_state.messages.append({"role": "assistant", "content": response})