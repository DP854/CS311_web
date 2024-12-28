# Dùng ChatGPT hỗ trợ cài đặt và chạy project
backend: mở Terminal => cd backend => pip install -r requirements.txt => uvicorn app:app --reload (chạy FastAPI)
frontend: mở Terminal thứ hai => cd frontend => npm install (sau khi đã cài NodeJS) => cài TailwindCSS => npm start (chạy React)

# Cấu trúc .env:
GEMINI_API_KEY=""
MONGO_URI=mongodb+srv://db_username:db_password@cluster0.qnexp.mongodb.net/db_name (Lấy link này trên MongoDB Cloud)
JWT_SECRET=mySuperSecretKey
JWT_ALGORITHM="HS256"
JWT_EXPIRATION=3600