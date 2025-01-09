from fastapi import FastAPI, UploadFile, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel 
from bson import ObjectId
from typing import List, Optional
import os
from utils import users_collection, hash_password, verify_password, create_jwt, decode_jwt, save_quiz, quizzes_collection, pinecone_index, embedding_model, pinecone_index, process_and_translate, clean_text
from langchain.prompts import PromptTemplate
from src.QAGenerator import model
import unicodedata

app = FastAPI()

security = HTTPBearer()

# Cấu hình CORS cho phép frontend từ mọi nguồn
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

class User(BaseModel):
    _id: str
    username: str
    password: str
    profile: Optional[dict] = {"email": "", "birthday": "","phone": "", "address": ""}
    quizzes: Optional[List[str]] = []
    pdfs_chat: Optional[List[str]] = []

    class Config:
        json_encoders = {
            ObjectId: str
        }

class Login(BaseModel):
    username: str
    password: str

class Quiz(BaseModel):
    _id: str
    quiz_name: str
    questions: List[dict]
    attempts: Optional[List[dict]] = [] # Lưu thông tin về các lần thử quiz của user

    class Config:
        json_encoders = {
            ObjectId: str
        }

class Question(BaseModel):
    question_text: str
    options: List[str]
    correct_answer: str

class ChatRequest(BaseModel):
    query: str
    pdf: Optional[str]

def get_current_user(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Token missing")
    
    token = authorization.split("Bearer ")[-1]

    if not token:
        raise HTTPException(status_code=401, detail="Token missing")
    
    user_data = decode_jwt(token)

    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    return user_data

# API đăng ký
@app.post("/api/register")
async def register_user(user: User):
    if users_collection.find_one({"username": user.username}):
        raise HTTPException(status_code=400, detail="Username đã tồn tại")

    password_hash = hash_password(user.password)
    users_collection.insert_one({
        "username": user.username,
        "password": password_hash,
        "profile": user.profile,
        "quizzes": [],
        "pdfs_chat": []
    })
    return {"message": "Đăng ký thành công"}

# API đăng nhập
@app.post("/api/login")
async def login_user(user: Login):
    db_user = users_collection.find_one({"username": user.username})
    
    if not db_user:
        raise HTTPException(status_code=400, detail="Tên người dùng không tồn tại")

    if not verify_password(user.password, db_user["password"]):
        raise HTTPException(status_code=400, detail="Mật khẩu không chính xác")

    token = create_jwt({"username": user.username}) 
    
    return {"token": token}


# API đăng xuất
@app.post("/api/logout")
async def logout():
    return {"message": "Đăng xuất thành công"}

# API lấy danh sách quizzes
@app.get("/api/quizzes", response_model=List[Quiz])
async def get_quizzes(current_user=Depends(get_current_user)):
    # Lấy thông tin người dùng từ cơ sở dữ liệu
    user = users_collection.find_one({"username": current_user["username"]})
    
    # Kiểm tra nếu người dùng không tồn tại
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Lấy danh sách các quiz_id của người dùng
    quiz_ids = user.get("quizzes", [])
    
    # Lọc các quiz từ quizzes_collection dựa trên quiz_id của người dùng
    all_quizzes = quizzes_collection.find()  # Lấy tất cả các quiz
    quizzes = [
        {**quiz, '_id': str(quiz['_id'])}  # Chuyển đổi _id thành chuỗi
        for quiz in all_quizzes if str(quiz['_id']) in quiz_ids
    ]
    
    return quizzes

# API thêm quiz
@app.post("/api/quizzes", response_model=Quiz)
async def create_quiz(quiz: Quiz, current_user=Depends(get_current_user)):
    # Lấy thông tin người dùng từ cơ sở dữ liệu
    user = users_collection.find_one({"username": current_user["username"]})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Kiểm tra nếu quiz đã tồn tại trong danh sách quizzes của người dùng
    if "quizzes" not in user or any(existing_quiz["_id"] == quiz._id for existing_quiz in user["quizzes"]):
        raise HTTPException(status_code=400, detail="Quiz đã tồn tại.")
    
    # Thêm quiz vào cơ sở dữ liệu
    result = quizzes_collection.insert_one(quiz.dict())
    quiz._id = str(result.inserted_id)

    # Thêm quiz mới vào danh sách quizzes của người dùng
    users_collection.update_one(
        {"username": current_user["username"]},
        {"$push": {"quizzes": quiz._id}}
    )

    return quiz

# API sửa quiz
@app.put("/api/quizzes/{quiz_name}", response_model=Quiz)
async def update_quiz(quiz_name: str, quiz: Quiz, current_user=Depends(get_current_user)):
    # Tìm người dùng hiện tại
    user = users_collection.find_one({"username": current_user["username"]})
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")
    
    # Giả sử user.get("quizzes", []) trả về danh sách các chuỗi
    quiz_ids = [ObjectId(id_str) for id_str in user.get("quizzes", [])]

    # Tìm quiz theo tên quiz và thuộc quyền sở hữu của người dùng
    existing_quiz = quizzes_collection.find_one({"quiz_name": quiz_name, "_id": {"$in": quiz_ids}})

    # Cập nhật quiz trong MongoDB
    quizzes_collection.update_one(
        {"_id": existing_quiz["_id"]},
        {"$set": {"questions": quiz.questions}}
    )
    
    existing_quiz["questions"] = quiz.questions
    return existing_quiz


# API xóa quiz
@app.delete("/api/quizzes/{quiz_name}")
async def delete_quiz(quiz_name: str, current_user=Depends(get_current_user)):
    # Tìm người dùng hiện tại
    user = users_collection.find_one({"username": current_user["username"]})
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")
    
    # Giả sử user.get("quizzes", []) trả về danh sách các chuỗi
    quiz_ids = [ObjectId(id_str) for id_str in user.get("quizzes", [])]

    # Tìm quiz theo tên quiz và thuộc quyền sở hữu của người dùng
    quiz = quizzes_collection.find_one({"quiz_name": quiz_name, "_id": {"$in": quiz_ids}})
    
    # Xóa quiz trong MongoDB
    quizzes_collection.delete_one({"_id": quiz["_id"]})
    
    # Xóa ID quiz khỏi danh sách `user.quizzes`
    users_collection.update_one(
        {"username": current_user["username"]},
        {"$pull": {"quizzes": str(quiz["_id"])}}
    )
    
    # Xóa tệp PDF tương ứng trong thư mục static
    file_location = os.path.join("static", f"{quiz_name}.pdf")
    if os.path.exists(file_location):
        os.remove(file_location)
    
    return {"message": f"Quiz '{quiz_name}' đã bị xóa thành công."}

#API xem quiz
@app.get("/api/quizzes/{quiz_name}")
async def get_quiz(quiz_name: str, current_user=Depends(get_current_user)):
    # Tìm người dùng hiện tại
    user = users_collection.find_one({"username": current_user["username"]})
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")
    
    # Giả sử user.get("quizzes", []) trả về danh sách các chuỗi
    quiz_ids = [ObjectId(id_str) for id_str in user.get("quizzes", [])]

    # Tìm quiz theo tên quiz và thuộc quyền sở hữu của người dùng
    quiz = quizzes_collection.find_one({"quiz_name": quiz_name, "_id": {"$in": quiz_ids}})

    quiz["_id"] = str(quiz["_id"])
    quiz["questions"] = quiz["questions"]
    
    return quiz

# API gửi bài làm quiz
@app.post("/api/quizzes/{quiz_name}/attempt")
async def attempt_quiz(quiz_name: str, answers: List[str], current_user=Depends(get_current_user)):
    quiz = quizzes_collection.find_one({"quiz_name": quiz_name})
    if not quiz:
        raise HTTPException(status_code=404, detail="Không tìm thấy quiz")

    # # Kiểm tra nếu câu trả lời là "True" hoặc "False", chuyển nó thành boolean
    # processed_answers = []
    # for ans in answers:
    #     if ans == "True":
    #         processed_answers.append(True)
    #     elif ans == "False":
    #         processed_answers.append(False)
    #     else:
    #         try:
    #             processed_answers.append(int(ans))  # Chuyển đổi chỉ mục thành số nguyên
    #         except ValueError:
    #             processed_answers.append(ans)  # Nếu không phải "True", "False" hay số, giữ nguyên
    
    # Tính điểm
    correct_answers = [q["answer"] for q in quiz["questions"]]
    score = sum(1 for i, ans in enumerate(answers) if ans == correct_answers[i])

    # Lưu kết quả làm quiz
    attempt = {
        "username": current_user["username"],
        "answers": answers,
        "score": score,
    }
    quizzes_collection.update_one(
        {"quiz_name": quiz_name},
        {"$push": {"attempts": attempt}}
    )

    return {"score": score, "total": len(correct_answers), "answers": correct_answers}

# API hiển thị lịch sử làm quiz
@app.get("/api/quizzes/{quiz_name}/history")
async def get_quiz_history(quiz_name: str, current_user=Depends(get_current_user)):
    quiz = quizzes_collection.find_one({"quiz_name": quiz_name})
    if not quiz:
        raise HTTPException(status_code=404, detail="Không tìm thấy quiz")

    history = [
        attempt for attempt in quiz.get("attempts", [])
        if attempt["username"] == current_user["username"]
    ]
    return history


# API xử lý PDF
@app.post("/upload")
async def upload_pdf(file: UploadFile, current_user=Depends(get_current_user)):
    # Tìm người dùng hiện tại
    user = users_collection.find_one({"username": current_user["username"]})
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")
    
    upload_folder = "static"
    
    #if not os.path.exists(upload_folder):
        #os.makedirs(upload_folder)
    user_folder = os.path.join(upload_folder, user["username"])
    
    # Tạo thư mục gốc và thư mục con nếu chưa tồn tại
    os.makedirs(user_folder, exist_ok=True)

    file_location = os.path.join(user_folder, file.filename)

    with open(file_location, "wb") as buffer:
        buffer.write(await file.read())

    return {"filename": file.filename, "file_location": file_location}

def convert_to_ascii(input_string):
    return unicodedata.normalize('NFKD', input_string).encode('ascii', 'ignore').decode('utf-8')

@app.post("/process-pdf-to-quiz")
async def process_pdf_to_quiz(file: UploadFile, current_user=Depends(get_current_user)):
    # Tìm người dùng hiện tại
    user = users_collection.find_one({"username": current_user["username"]})
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")
    
    upload_folder = "static"
    #if not os.path.exists(upload_folder):
        #os.makedirs(upload_folder)
    user_folder = os.path.join(upload_folder, user["username"])
    
    # Tạo thư mục gốc và thư mục con nếu chưa tồn tại
    os.makedirs(user_folder, exist_ok=True)

    file_location = os.path.join(user_folder, file.filename)

    # Kiểm tra nếu tệp đã tồn tại, xóa nó đi trước khi lưu tệp mới
    if os.path.exists(file_location):
        os.remove(file_location)
    
    # Lưu file PDF
    with open(file_location, "wb") as buffer:
        buffer.write(await file.read())
    
    await save_quiz(file_location, user)

@app.post("/process-pdf-to-chat")
async def process_pdf_to_chat(file: UploadFile, current_user=Depends(get_current_user)):
    # Tìm người dùng hiện tại
    user = users_collection.find_one({"username": current_user["username"]})
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")
    
    upload_folder = "static"
    user_folder = os.path.join(upload_folder, user["username"])
    
    # Tạo thư mục gốc và thư mục con nếu chưa tồn tại
    os.makedirs(user_folder, exist_ok=True)

    file_location = os.path.join(user_folder, file.filename)

    # Lưu file PDF
    with open(file_location, "wb") as buffer:
        buffer.write(await file.read())
    
    # Tải và xử lý nội dung PDF
    processed_documents = await process_and_translate(file_location)

    text = "\n".join([doc["page_content"] for doc in processed_documents])
    
    text = clean_text(text)

    # Chia nội dung theo trang
    chunks = []
    current_chunk = ""
    page_number = None

    for doc in processed_documents:
        if doc["page_number"] != page_number:
            if current_chunk:
                chunks.append({
                    "text": current_chunk,
                    "page_number": page_number
                })
            current_chunk = doc["page_content"]
            page_number = doc["page_number"]
        else:
            current_chunk += "\n" + doc["page_content"]
    if current_chunk:
        chunks.append({
            "text": current_chunk,
            "page_number": page_number
        })
        
    # Chuyển đổi filename sang ASCII
    ascii_filename = convert_to_ascii(file.filename)
    
    for i, chunk in enumerate(chunks):
        embedding = embedding_model.encode(chunk["text"]).tolist()
        
        # Tạo vector ID
        vector_id = f"{user["username"]}_{ascii_filename}_{i}"
        
        # Lưu vector vào Pinecone
        pinecone_index.upsert(
            vectors=[(vector_id, embedding, {"metadata": chunk["text"], "page_number": chunk["page_number"]})],
            namespace=f"{user["username"]}.{ascii_filename}",
        )

    # Lưu tên PDF vào users.collection
    users_collection.update_one(
        {"username": user["username"]},
        {"$addToSet": {"pdfs_chat": ascii_filename}},
        upsert=True
    )

@app.get("/user-pdfs-chat")
async def get_user_pdfs_chat(current_user=Depends(get_current_user)):
    # Tìm người dùng hiện tại
    user = users_collection.find_one({"username": current_user["username"]})
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")
    
    pdfs = user["pdfs_chat"]  # Lấy danh sách PDF từ thông tin người dùng
    return {"pdfs": pdfs}   

@app.post("/chat")
async def chat_with_pdf(request: ChatRequest, current_user=Depends(get_current_user)):
    # Tìm người dùng hiện tại
    user = users_collection.find_one({"username": current_user["username"]})
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")
    try:
        query = request.query
        query_embedding = embedding_model.encode(query).tolist()

        search_results = []
        if(request.pdf) :
            search_results = pinecone_index.query(
                namespace=f"{user["username"]}.{request.pdf}",
                vector=query_embedding, 
                top_k=5, 
                include_metadata=True
                )
        # Nếu người dùng không chọn PDF hoặc không có PDF thì tìm trong namespace mặc định
        else :
            search_results = pinecone_index.query(
                namespace=f"",
                vector=query_embedding, 
                top_k=4, 
                include_metadata=True
                )
        
        # context = "\n".join(match.metadata["metadata"] for match in search_results["matches"])
        # Thay thế phần xử lý context
        context = "\n".join(
            str(match.metadata.get("metadata", "")) 
            for match in search_results.get("matches", [])
        )
        
        # Tạo một dictionary chỉ với các thông tin cần thiết
        formatted_results = [
            {
                "id": match.get("id", ""),
                "score": match.get("score", 0),
                "metadata": match.metadata.get("metadata", "")  # Chỉ lấy metadata cần thiết
            }
            for match in search_results.get("matches", [])
        ]
        
        prompt = (
                    f"Context:\n{context}\n\n"
                    f"User Query:\n{query}\n\n"
                    f"Instructions:\n"
                    f"1. Provide a clear and concise response to the user's query based on the provided context.\n"
                    f"2. Ensure the response is formatted for display in a report, not includes any specific character like (**) and adhering to react-markdown syntax.\n"
                    f"3. If additional information is required or the query cannot be answered fully, provide a helpful and polite clarification to the user \n\n"
                    f"Example format:\n"
                    f"Respond by saying that the answer to the question has been found, and smoothly lead into the answer\n"
                    f"1. Any subtitle\n"
                    f"2. Next subtitle\n"
                    f"3. ....\n"
                    f"Consume and condition!\n"
                    f"Additionally, offer related follow-up questions to guide the user further. \n\n"
                    f"Response:\n"
        )
        question_prompt = PromptTemplate(
                        template=prompt,
                        input_variables=["context", "query"]
        )
        formatted_prompt = question_prompt.format(context=context, query=query)
        response = (
                    model.generate_content(formatted_prompt).candidates[0].content.parts[0].text
                    if formatted_results != []
                    else "I am a chatbot designed to answer questions about the PDF you have provided. \
                        Your question does not fall within the system's setup or may not be related to \
                        the content of the PDF you uploaded. Please ask another question, \
                        and I will assist you."
        )
        return { 
            "response": response,
            "search_results": formatted_results if formatted_results != [] else "Không có dữ liệu từ search"
        }
    except Exception as e:
        return { "error": str(e) }