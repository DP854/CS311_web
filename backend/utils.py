import os
import csv
from dotenv import load_dotenv
from pymongo import MongoClient
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from src.QAGenerator import generate_question_from_chunks
from passlib.context import CryptContext
import jwt
from datetime import datetime, timedelta
from bson import ObjectId

load_dotenv()

# Băm password
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password):
    return pwd_context.hash(password)

def verify_password(password, hashed_password):
    return pwd_context.verify(password, hashed_password)

# JWT token handling
jwt_secret = os.getenv("JWT_SECRET")
jwt_algorithm = os.getenv("JWT_ALGORITHM")
jwt_expiration = int(os.getenv("JWT_EXPIRATION"))

def create_jwt(data: dict):
    expiration = datetime.utcnow() + timedelta(minutes=jwt_expiration)
    data.update({"exp": expiration})
    return jwt.encode(data, jwt_secret, algorithm=jwt_algorithm)

def decode_jwt(token: str):
    try:
        decoded_token = jwt.decode(token, jwt_secret, algorithms=[jwt_algorithm])
        exp_timestamp = decoded_token.get("exp", None)

        if exp_timestamp is None:
            return None
        
        if exp_timestamp < datetime.utcnow().timestamp():
            return None
        
        return decoded_token
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

# Kết nối tới MongoDB Cloud
client = MongoClient(os.getenv('MONGO_URI'))
db = client.get_database() 
users_collection = db.users
quizzes_collection = db.quizzes 

# Xử lý PDF
def file_processing(file_path):
    loader = PyPDFLoader(file_path)
    data = loader.load()

    question_gen = ''
    max_token = 5012

    for page in data:
        question_gen += page.page_content

    splitter_ques_gen = RecursiveCharacterTextSplitter(
        chunk_size=max_token,
        chunk_overlap=200
    )

    chunks_ques_gen = splitter_ques_gen.split_text(question_gen)

    document_ques_gen = [Document(page_content=t) for t in chunks_ques_gen]

    return document_ques_gen

def llm_pipeline(file_path):
    document_ques_gen = file_processing(file_path)
    quiz = generate_question_from_chunks(document_ques_gen)
    return quiz

# Lưu quiz vào MongoDB
def save_to_mongo(quiz_data, quiz_name, user):
    # Giả sử user.get("quizzes", []) trả về danh sách các chuỗi
    quiz_ids = [ObjectId(id_str) for id_str in user.get("quizzes", [])]

    # Tìm quiz theo tên quiz và thuộc quyền sở hữu của người dùng
    existing_quiz = quizzes_collection.find_one({"quiz_name": quiz_name, "_id": {"$in": quiz_ids}})

    # Kiểm tra xem quiz đã tồn tại chưa, nếu tồn tại thì update, nếu không thì insert
    if existing_quiz:
        quizzes_collection.update_one(
            {"_id": existing_quiz["_id"], "quiz_name": quiz_name},
            {"$set": {"questions": quiz_data}},
        )
    else:
        result = quizzes_collection.insert_one({
            "quiz_name": quiz_name,
            "questions": quiz_data
        })  
        id = str(result.inserted_id)

        users_collection.update_one(
            {"username": user["username"]},
            {"$push": {"quizzes": id}}
        )

def get_csv(file_path, user):
    ques_list = llm_pipeline(file_path)
    
    # Chuyển đổi câu hỏi thành dạng quiz
    quiz_data = []
    for question in ques_list:
        quiz_data.append({
            "question": question['question'],  # Lấy câu hỏi
            "options": question['options'],    # Lấy các lựa chọn
            "answer": question['answer']       # Lấy câu trả lời
        })
    
    base_folder = 'static/'
    if not os.path.isdir(base_folder):
        os.mkdir(base_folder)
    quiz_name = os.path.splitext(os.path.basename(file_path))[0]
    output_file = os.path.join(base_folder, f"{quiz_name}.csv")
    
    # Lưu quiz đầy đủ vào MongoDB (bao gồm nhiều câu hỏi)
    save_to_mongo(quiz_data, quiz_name, user)
    
    # Lưu dữ liệu thành file CSV
    with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(["Question", "Answer"])

        for question in ques_list:
            csv_writer.writerow([question['question'], question['answer']])

    return output_file
