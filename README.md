# Cài đặt và chạy project
<p>backend: mở Terminal => cd backend => pip install -r requirements.txt => uvicorn app:app --reload (chạy FastAPI)</p>
<p>frontend: mở Terminal thứ hai => cd frontend => npm install (sau khi đã cài NodeJS) => cài TailwindCSS => npm start (chạy React)</p>

# Feature
<p>Đăng ký, Đăng nhập, Đăng xuất</p>
<p>CRUD quiz</p>
<p>Làm bài quiz</p>
<p>Upload PDF sang quiz (LangChain): Dùng dữ liệu văn bản (Sau khi kiểm tra dữ liệu mô tả hình ảnh và mô tả bảng biểu thì nó tạo rất nhiều câu hỏi vô nghĩa, ví dụ như câu hỏi giá trị dữ liệu trong bảng hay câu hỏi có gì trong hình mà không liên quan đến nội dung chính trong PDF. Vì thế tôi quyết định không cho dữ liệu này vào pineline quiz)</p>
<p>Chat với PDF (LangChain + Gemini + SentenceTransformer + PineCone): Dùng dữ liệu văn bản, mô tả hình ảnh, mô tả bảng biểu</p>

# Bổ sung
<p>Cài thêm tesseract vào máy: https://github.com/tesseract-ocr/tesseract/releases/download/5.5.0/tesseract-ocr-w64-setup-5.5.0.20241111.exe</p>
<p>pip install PyMuPDF pytesseract camelot-py[cv]</p>
