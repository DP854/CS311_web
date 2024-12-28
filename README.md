# Dùng ChatGPT hỗ trợ cài đặt và chạy project
<p>backend: mở Terminal => cd backend => pip install -r requirements.txt => uvicorn app:app --reload (chạy FastAPI)</p>
<p>frontend: mở Terminal thứ hai => cd frontend => npm install (sau khi đã cài NodeJS) => cài TailwindCSS => npm start (chạy React)</p>

# Cấu trúc .env:
<p>GEMINI_API_KEY=""</p>
<p>MONGO_URI=mongodb+srv://db_username:db_password@cluster0.qnexp.mongodb.net/db_name (Lấy link này trên MongoDB Cloud)</p>
<p>JWT_SECRET=mySuperSecretKey</p>
<p>JWT_ALGORITHM="HS256"</p>
<p>JWT_EXPIRATION=3600</p>

# Feature
<p>Đăng ký, Đăng nhập, Đăng xuất</p>
<p>CRUD quiz</p>
<p>Làm bài quiz</p>
<p>Upload PDF sang quiz (LangChain)</p>
