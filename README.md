# How to Set Up

### Backend Setup
1. Open a terminal and navigate to the backend folder:
   ```bash
   cd backend
   ```
2. Install the required Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Start the FastAPI server:
   ```bash
   uvicorn app:app --reload
   ```

### Frontend Setup
1. Open a second terminal and navigate to the frontend folder:
   ```bash
   cd frontend
   ```
2. Install Node.js dependencies (ensure Node.js is installed):
   ```bash
   npm install
   ```
3. Install TailwindCSS.
4. Start the React development server:
   ```bash
   npm start
   ```

### Additional Setup
1. Install Tesseract OCR on your system:
   [Download Tesseract OCR](https://github.com/tesseract-ocr/tesseract/releases/download/5.5.0/tesseract-ocr-w64-setup-5.5.0.20241111.exe)
2. Install additional Python packages:
   ```bash
   pip install PyMuPDF pytesseract camelot-py[cv]
   ```


# Features

### 1. Authentication
- User can **Register**, **Log In**, and **Log Out**.

### 2. Quiz Management
- Full **CRUD** operations for quizzes, allowing users to create, read, update, and delete quizzes.

### 3. Quiz Participation
- Users can **take quizzes** and submit their answers.

### 4. PDF to Quiz Conversion (LangChain)
- Converts **textual data** from PDFs into quizzes.
- **Exclusion of specific data types:** After analyzing the content, questions generated from image descriptions and table data often lack meaningful context (e.g., questions about table values or unrelated image content). These data types are excluded from the quiz generation pipeline.

### 5. Chat with PDF
- Features powered by **LangChain**, **Gemini**, **SentenceTransformer**, and **Pinecone**.
- Supports interaction with:
  - **Textual data** from the PDF.
  - **Image descriptions** extracted from the PDF.
  - **Table data** extracted from the PDF.
