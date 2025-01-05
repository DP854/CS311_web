import os
import csv
from dotenv import load_dotenv
from pymongo import MongoClient
import re
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from src.QAGenerator import generate_question_from_chunks
from passlib.context import CryptContext
import jwt
from datetime import datetime, timedelta
from bson import ObjectId
import asyncio
from googletrans import Translator
from langdetect import detect
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer

load_dotenv()

# Pinecone
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"), environment="us-east-1")
index_name = os.getenv("PINECONE_INDEX_NAME")
pinecone_index = pc.Index(index_name)

# Embedding model
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

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

    # Loại bỏ xuống dòng không cần thiết trong đoạn văn
    question_gen = re.sub(r"(?<!\n)\n(?!\n)", " ", question_gen)

    # Tách các phần quan trọng (tiêu đề, danh sách, bảng)
    question_gen = re.sub(r"(\n{2,})", "\n\n", question_gen)  # Chuẩn hóa ngắt dòng
    question_gen = re.sub(r"(?<=\w)-\s+", "", question_gen)  # Gộp các từ bị phân mảnh

    # Chia nhỏ văn bản thành các đoạn có kích thước nhỏ hơn
    splitter_ques_gen = RecursiveCharacterTextSplitter(
        chunk_size=max_token,
        chunk_overlap=200
    )
    chunks_ques_gen = splitter_ques_gen.split_text(question_gen)

    # Tạo các Document từ các đoạn đã chia
    document_ques_gen = [Document(page_content=t) for t in chunks_ques_gen]

    return document_ques_gen

#Chuyển text qua tiếng anh
async def translate_text(document_ques_gen):
    translator = Translator()
    
    # Phát hiện ngôn ngữ của văn bản
    detected_lang = detect(document_ques_gen)
    
    # Nếu ngôn ngữ là tiếng Việt, tiến hành dịch sang tiếng Anh
    if detected_lang == 'vi':
        translated_text = await translator.translate(document_ques_gen, src='vi', dest='en')
        return translated_text.text
    else:
        # Nếu ngôn ngữ không phải là tiếng Việt, trả về văn bản gốc
        return document_ques_gen

#Chuyển text qua tiếng anh
async def translate_documents(documents):
    # Lặp qua từng document và dịch nội dung
    translated_documents = []
    
    for document in documents:
        page_content = document.page_content  # Lấy nội dung trang
        translated_text = await translate_text(page_content)  # Dịch nội dung trang
        translated_documents.append(translated_text)  # Lưu kết quả dịch vào danh sách
    
    return translated_documents

async def process_and_translate(file_path):
    document_ques_gen = file_processing(file_path) 
    translated_documents = await translate_documents(document_ques_gen)
    return translated_documents

async def llm_pipeline(file_path):
    document_ques_gen = file_processing(file_path) 
    translated_documents = await translate_documents(document_ques_gen)
    # quiz = generate_question_from_chunks(document_ques_gen)
    # Thêm từng chunk vào model để xử lí
    quiz_from_chunk = []
    for text in translated_documents:
        quizz = generate_question_from_chunks(text)
        quiz_from_chunk += quizz
    return quiz_from_chunk

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

# Save questions to CSV
async def get_csv(file_path, user):
    ques_list = await llm_pipeline(file_path)  # Await the LLM pipeline
    
    # Convert questions into quiz format
    quiz_data = []
    for question in ques_list:
        quiz_data.append({
            "question": question['question'],  # Extract the question
            "options": question['options'],    # Extract the options
            "answer": str(question['answer'])  # Convert answer to string ('True' or 'False')
        })

    base_folder = 'static/'
    if not os.path.isdir(base_folder):
        os.mkdir(base_folder)
    quiz_name = os.path.splitext(os.path.basename(file_path))[0]
    output_file = os.path.join(base_folder, f"{quiz_name}.csv")
    
    # Save the quiz to MongoDB (including all questions)
    save_to_mongo(quiz_data, quiz_name, user)
    
    # Save the data to a CSV file
    with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(["Question", "Answer"])

        for question in ques_list:
            # Convert the boolean answer to string for the CSV file
            csv_writer.writerow([question['question'], str(question['answer'])])

    return output_file


