import streamlit as st
import os
import time
import pandas as pd
import google.generativeai as genai
import matplotlib.pyplot as plt
import json
from dotenv import load_dotenv
from io import StringIO, BytesIO
from PIL import Image

# Tải các biến môi trường từ file .env
load_dotenv()

# --- Cấu hình trang Streamlit ---
st.set_page_config(
    page_title="Smart Chat App",
    page_icon="🤖",
    layout="wide"
)

# --- Cấu hình Gemini API ---
def configure_gemini():
    """Cấu hình và trả về model Gemini."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        st.error("GOOGLE_API_KEY không được tìm thấy trong file .env. Vui lòng thêm API Key của bạn.")
        st.stop()
    
    genai.configure(api_key=api_key)
    try:
        model = genai.GenerativeModel('gemini-flash-latest')
        return model
    except Exception as e:
        st.error(f"Không thể khởi tạo model Gemini. Lỗi: {e}")
        st.stop()

model = configure_gemini()

# --- Quản lý Trạng thái Phiên (Session State) ---
def initialize_session_state():
    """Khởi tạo các giá trị cần thiết trong session state."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "uploaded_image" not in st.session_state:
        st.session_state.uploaded_image = None
    if "dataframe" not in st.session_state:
        st.session_state.dataframe = None
    if "dataframe_name" not in st.session_state:
        st.session_state.dataframe_name = ""

initialize_session_state()

# --- HÀM MỚI: TẠO BIỂU ĐỒ ---
def create_plot(plot_info):
    """
    Tạo biểu đồ bằng Matplotlib dựa trên thông tin từ AI.
    Trả về một đối tượng BytesIO chứa hình ảnh của biểu đồ.
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
                ax.set_title(f"Biểu đồ phân phối của cột '{column}'")
                ax.set_xlabel(column)
                ax.set_ylabel("Tần suất")
            else:
                return f"Lỗi: Không tìm thấy cột '{column}'."

        elif plot_type == "bar":
            x_col = plot_info.get("x_column")
            y_col = plot_info.get("y_column")
            if x_col in df.columns and y_col in df.columns:
                # Lấy 15 giá trị hàng đầu để biểu đồ không quá đông đúc
                top_data = df.nlargest(15, y_col).sort_values(y_col, ascending=False)
                ax.bar(top_data[x_col], top_data[y_col])
                ax.set_title(f"Biểu đồ cột so sánh '{x_col}' và '{y_col}'")
                ax.set_xlabel(x_col)
                ax.set_ylabel(y_col)
                plt.xticks(rotation=45, ha="right")
            else:
                return f"Lỗi: Không tìm thấy cột '{x_col}' hoặc '{y_col}'."
        
        else:
            return f"Lỗi: Loại biểu đồ '{plot_type}' không được hỗ trợ."

        plt.tight_layout()
        buf = BytesIO()
        fig.savefig(buf, format="png")
        buf.seek(0)
        plt.close(fig)
        return buf

    except Exception as e:
        plt.close(fig)
        return f"Lỗi khi vẽ biểu đồ: {e}"

# --- Hàm tương tác với Gemini API (Cập nhật Prompt) ---
def get_gemini_response_stream(user_message, image_bytes=None, dataframe=None):
    """
    Hàm này gọi đến Google Gemini API và trả về một generator để stream phản hồi.
    """
    try:
        contents = []
        prompt = user_message

        # --- CẬP NHẬT PROMPT CHO CSV ---
        if dataframe is not None:
            df_info_summary = f"Dữ liệu CSV có các cột: {', '.join(dataframe.columns.tolist())}."
            
            # Hướng dẫn AI cách yêu cầu vẽ đồ thị
            plotting_instruction = (
                "QUAN TRỌNG: Nếu người dùng yêu cầu vẽ biểu đồ (plot, chart, graph, draw, vẽ, biểu diễn), "
                "bạn CHỈ được trả lời bằng một chuỗi JSON duy nhất, không có giải thích hay định dạng markdown.\n"
                "Các định dạng JSON được hỗ trợ:\n"
                "1. Biểu đồ phân phối: {\"plot\": {\"type\": \"histogram\", \"column\": \"tên_cột\"}}\n"
                "2. Biểu đồ cột: {\"plot\": {\"type\": \"bar\", \"x_column\": \"tên_cột_x\", \"y_column\": \"tên_cột_y\"}}\n"
                "Nếu không, hãy trả lời câu hỏi của người dùng như một chuyên gia phân tích dữ liệu."
            )
            
            prompt = (
                f"{plotting_instruction}\n\n"
                f"Thông tin về dữ liệu: {df_info_summary}\n"
                f"Câu hỏi của người dùng: '{user_message}'"
            )
        
        # ... (logic xử lý ảnh giữ nguyên) ...
        if image_bytes:
            image = Image.open(BytesIO(image_bytes))
            if not prompt:
                prompt = "Mô tả chi tiết bức ảnh này."
            contents = [prompt, image]
        else:
            contents = [prompt]
            
        response_stream = model.generate_content(contents, stream=True)
        
        for chunk in response_stream:
            if chunk.parts:
                yield chunk.text

    except Exception as e:
        yield f"Xin lỗi, tôi gặp sự cố khi tạo phản hồi. Lỗi: {e}"


# --- Giao diện người dùng (UI) ---
# ... (Phần UI và session state giữ nguyên, chỉ thay đổi logic xử lý phản hồi) ...
st.title("🤖 Chat App Đa Năng")
st.write("Trò chuyện, phân tích ảnh và dữ liệu CSV với sức mạnh của Google Gemini.")

col1, col2 = st.columns([1, 2])

with col1:
    st.header("Bảng điều khiển")
    if st.button("🗑️ Xóa cuộc trò chuyện"):
        # ... (logic nút xóa giữ nguyên) ...
        st.session_state.messages, st.session_state.uploaded_image, st.session_state.dataframe, st.session_state.dataframe_name = [], None, None, ""
        st.rerun()

    with st.expander("🖼️ Chat với Ảnh", expanded=True):
        # ... (logic tải ảnh giữ nguyên) ...
        uploaded_image_file = st.file_uploader("Tải lên một hình ảnh", type=["png", "jpg", "jpeg"], label_visibility="collapsed")
        if uploaded_image_file:
            image_bytes = uploaded_image_file.getvalue()
            if st.session_state.uploaded_image != image_bytes:
                st.session_state.uploaded_image = image_bytes
                st.session_state.messages.append({"role": "system_info", "content": "Một hình ảnh đã được tải lên.", "image": image_bytes})
                st.rerun()
        if st.session_state.uploaded_image:
            st.image(st.session_state.uploaded_image, caption="Ảnh đang được phân tích")

    with st.expander("📊 Chat với Dữ liệu CSV", expanded=True):
        # ... (logic tải CSV giữ nguyên) ...
        if st.session_state.dataframe_name:
            st.info(f"Đang chat với: {st.session_state.dataframe_name}")
            if st.button("Xóa dữ liệu CSV"):
                st.session_state.dataframe, st.session_state.dataframe_name = None, ""
                st.session_state.messages.append({"role": "system_info", "content": "Dữ liệu CSV đã được xóa."})
                st.rerun()
        uploaded_csv_file = st.file_uploader("Tải lên file CSV", type="csv", key="csv_upload")
        csv_url = st.text_input("Hoặc dán URL đến file CSV", key="csv_url_input")
        if st.button("Xử lý CSV", key="process_csv_button"):
            with st.spinner("Đang đọc và phân tích CSV..."):
                try:
                    df, file_name = (pd.read_csv(uploaded_csv_file), uploaded_csv_file.name) if uploaded_csv_file else (pd.read_csv(csv_url), csv_url.split('/')[-1]) if csv_url else (None, "")
                    if df is not None:
                        st.session_state.dataframe, st.session_state.dataframe_name = df, file_name
                        st.session_state.messages.append({"role": "system_info", "content": f"Đã tải thành công file '{file_name}' với {df.shape[0]} dòng và {df.shape[1]} cột."})
                        st.rerun()
                    else: st.warning("Vui lòng tải file hoặc cung cấp URL.")
                except Exception as e: st.error(f"Lỗi khi đọc CSV: {e}")

with col2:
    chat_container = st.container(height=600)
    with chat_container:
        for message in st.session_state.messages:
            role = message["role"]
            avatar = "ℹ️" if role == "system_info" else "👤" if role == "user" else "🤖"
            with st.chat_message(role, avatar=avatar):
                if "image" in message:
                    st.image(message["image"], width=200)
                if "content" in message:
                    st.markdown(message["content"])

    if prompt := st.chat_input("Nhập câu hỏi của bạn..."):
        user_message_entry = {"role": "user", "content": prompt}
        if st.session_state.uploaded_image: user_message_entry["image"] = st.session_state.uploaded_image
        st.session_state.messages.append(user_message_entry)
        
        with chat_container:
             with st.chat_message("user", avatar="👤"):
                if "image" in user_message_entry: st.image(user_message_entry["image"], width=200)
                st.markdown(user_message_entry["content"])

        # --- CẬP NHẬT LOGIC XỬ LÝ PHẢN HỒI ---
        with chat_container:
            with st.chat_message("assistant", avatar="🤖"):
                with st.spinner("AI đang suy nghĩ... 🤔"):
                    response_generator = get_gemini_response_stream(
                        prompt, st.session_state.uploaded_image, st.session_state.dataframe
                    )
                    # Gom các chunk lại thành một phản hồi đầy đủ
                    full_response = "".join([chunk for chunk in response_generator])

                # KIỂM TRA XEM PHẢN HỒI CÓ PHẢI LÀ YÊU CẦU VẼ ĐỒ THỊ KHÔNG
                is_plot_request = False
                try:
                    # Cố gắng phân tích chuỗi JSON
                    json_response = json.loads(full_response)
                    if "plot" in json_response:
                        is_plot_request = True
                        with st.spinner("Đang vẽ biểu đồ... 🎨"):
                            plot_image_buffer = create_plot(json_response["plot"])
                            if isinstance(plot_image_buffer, BytesIO):
                                st.image(plot_image_buffer, caption="Biểu đồ được tạo bởi AI")
                                st.session_state.messages.append({"role": "assistant", "image": plot_image_buffer, "content": "Đây là biểu đồ bạn yêu cầu:"})
                            else: # Nếu hàm create_plot trả về chuỗi lỗi
                                st.error(plot_image_buffer)
                                st.session_state.messages.append({"role": "assistant", "content": plot_image_buffer})
                except json.JSONDecodeError:
                    # Nếu không phải JSON, thì đó là văn bản bình thường
                    is_plot_request = False
                
                # Nếu không phải yêu cầu vẽ đồ thị, hiển thị văn bản như cũ
                if not is_plot_request:
                    st.markdown(full_response)
                    st.session_state.messages.append({"role": "assistant", "content": full_response})

        st.session_state.uploaded_image = None