import os
from dotenv import load_dotenv
from pymongo import MongoClient
import re
from langchain_community.document_loaders import PyPDFLoader
from PIL import Image
import pytesseract, fitz, camelot, io
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from src.QAGenerator import generate_question_from_chunks
from passlib.context import CryptContext
import jwt
from datetime import datetime, timedelta
from bson import ObjectId
from googletrans import Translator
from langdetect import detect
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer

load_dotenv()

# Pytesseract config
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Pinecone
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"), environment="us-east-1")
index_name = os.getenv("PINECONE_INDEX_NAME")
pinecone_index = pc.Index(index_name)

# Embedding model
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

def clean_text(text):
    # Loại bỏ các ký tự không mong muốn, như chuỗi '.' dài
    text = re.sub(r'[\.\-\_]{2,}', '', text)
    
    # Loại bỏ các ký tự không phải chữ cái, số, hoặc ký tự cơ bản
    text = re.sub(r'[^a-zA-Z0-9\s,.!?\'"()%-]', '', text)
    
    # Thay nhiều khoảng trắng liên tiếp bằng một khoảng trắng
    text = re.sub(r'\s{2,}', ' ', text)
    
    # Loại bỏ khoảng trắng đầu và cuối
    return text.strip()

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

# Ảnh sang text
def extract_text_from_image(file_path):
    doc = fitz.open(file_path)
    image_text = []
    page_text = ""

    for page_number in range(len(doc)):
        page = doc[page_number]
        images = page.get_images(full=True)

        for img_index, img in enumerate(images):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image = Image.open(io.BytesIO(image_bytes))

            page_text += f"(Image {img_index + 1}):\n"
            page_text += pytesseract.image_to_string(image)

        if page_text.strip():
            image_text.append({"text": page_text, "page_number": page_number + 1})

    return image_text

# Bảng sang text
def extract_text_from_table(file_path):
    tables = camelot.read_pdf(file_path, pages="all")
    table_text = []
    table_count = 1

    for table in tables:
        page_number = table.page
        table_text.append({"text": f"(Table {table_count}):\n" + table.df.to_string(), "page_number": page_number})
        table_count += 1

    return table_text

# Xử lý PDF để tạo quiz
def file_processing_quiz(file_path):
    loader = PyPDFLoader(file_path)
    data = loader.load()

    question_gen = ""

    for page in data:
        question_gen += page.page_content

    # Loại bỏ xuống dòng không cần thiết trong đoạn văn
    question_gen = re.sub(r"(?<!\n)\n(?!\n)", " ", question_gen)

    # Tách các phần quan trọng (tiêu đề, danh sách, bảng)
    question_gen = re.sub(r"(\n{2,})", "\n\n", question_gen)  # Chuẩn hóa ngắt dòng
    question_gen = re.sub(r"(?<=\w)-\s+", "", question_gen)  # Gộp các từ bị phân mảnh

    # Chia nhỏ văn bản thành các đoạn có kích thước nhỏ hơn
    splitter_ques_gen = RecursiveCharacterTextSplitter(
        chunk_size=5012,
        chunk_overlap=200
    )
    chunks_ques_gen = splitter_ques_gen.split_text(question_gen)

    # Tạo các Document từ các đoạn đã chia
    document_ques_gen = [Document(page_content=t) for t in chunks_ques_gen]

    return document_ques_gen    

# Xử lý PDF cho chatbot
def file_processing_chat(file_path):
    loader = PyPDFLoader(file_path)
    data = loader.load()

    document_ques_gen = []

    # Trích xuất văn bản từ ảnh
    image_text = extract_text_from_image(file_path)

    # Trích xuất văn bản từ bảng
    table_text = extract_text_from_table(file_path)

    page_number = 1

    # Duyệt qua từng trang của PDF
    for page in data:
        page_content = page.page_content

        # Gắn text từ image ở trang hiện tại
        for img_text in image_text:
            if img_text["page_number"] == page_number:
                page_content += "\n" + img_text["text"]

        # Gắn text từ bảng ở trang hiện tại
        for tab_text in table_text:
            if tab_text["page_number"] == page_number:
                page_content += "\n" + tab_text["text"] 
        
        # Xử lý văn bản
        page_content = re.sub(r"(?<!\n)\n(?!\n)", " ", page_content)
        page_content = re.sub(r"(\n{2,})", "\n\n", page_content)
        page_content = re.sub(r"(?<=\w)-\s+", "", page_content)

        splitter_ques_gen = RecursiveCharacterTextSplitter(
            chunk_size=5012,
            chunk_overlap=200
        )
        chunks = splitter_ques_gen.split_text(page_content)

        for chunk in chunks:
            doc = Document(
                page_content=chunk,
                metadata={"page_number": page_number}
            )
            document_ques_gen.append(doc)

        page_number += 1

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

async def translate_documents_quiz(documents):
    # Lặp qua từng document và dịch nội dung
    translated_documents = []
    
    for document in documents:
        page_content = document.page_content  # Lấy nội dung trang
        translated_text = await translate_text(page_content)  # Dịch nội dung trang
        translated_documents.append(translated_text)  # Lưu kết quả dịch vào danh sách
    
    return translated_documents

#Chuyển doc qua tiếng anh
async def translate_documents_chat(documents):
    # Lặp qua từng document và dịch nội dung
    translated_documents = []
    
    for document in documents:
        page_content = document.page_content  # Lấy nội dung trang
        translated_text = await translate_text(page_content)  # Dịch nội dung trang
        # translated_documents.append(translated_text)  # Lưu kết quả dịch vào danh sách
        translated_documents.append({
            'page_content': translated_text,
            'page_number': document.metadata.get("page_number", None)
        })
    
    return translated_documents

async def process_and_translate_chat(file_path):
    document_ques_gen = file_processing_chat(file_path) 
    translated_documents = await translate_documents_chat(document_ques_gen)
    return translated_documents

async def llm_pipeline_quiz(file_path):
    document_ques_gen = file_processing_quiz(file_path) 
    translated_documents = await translate_documents_quiz(document_ques_gen)
    # Thêm từng chunk vào model để xử lí
    quiz_from_chunk = []
    for text in translated_documents:
        quiz = generate_question_from_chunks(text)
        quiz_from_chunk += quiz
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

# Save questions to quiz
async def save_quiz(file_path, user):
    ques_list = await llm_pipeline_quiz(file_path)  # Await the LLM pipeline
    
    # Convert questions into quiz format
    quiz_data = []
    for question in ques_list:
        if type(question) == dict:
            quiz_data.append({
                "question": question['question'],  # Extract the question
                "options": question['options'],    # Extract the options
                "answer": str(question['answer'])  # Convert answer to string ('True' or 'False')
            })

    quiz_name = os.path.splitext(os.path.basename(file_path))[0]
    
    # Save the quiz to MongoDB (including all questions)
    save_to_mongo(quiz_data, quiz_name, user)


