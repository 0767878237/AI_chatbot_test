# Yêu cầu cần có
Python 3.8 trở lên, pip

# git
git clone https://github.com/0767878237/AI_chatbot_test.git -> cd your-project-directory

# Tạo và kích hoạt môi trường ảo
# Window:
python -m venv venv -> .\venv\Scripts\activate

# macOS/Linux:
python3 -m venv venv -> source venv/bin/activate

# Chạy lệnh sau để cài tất cả thư viện (cài ở môi trường ảo):
pip install -r requirements.txt

# Cấu hình gemini api key
tạo file .env -> thêm dòng GOOGLE_API_KEY="YOUR_API_KEY_HERE" -> thay thế YOUR_API_KEY_HERE bằng API Key của bạn (https://aistudio.google.com/app/api-keys)

# Chạy ứng dụng
streamlit run app.py
