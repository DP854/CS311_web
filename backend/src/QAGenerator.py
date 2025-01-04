from langchain.prompts import PromptTemplate
import google.generativeai as genai
import os
from dotenv import load_dotenv
import json 

# Load API key from .env file 
load_dotenv()
gemini_api_key = os.getenv("GEMINI_API_KEY")

# Configure the Generative AI model
genai.configure(api_key=gemini_api_key)
model = genai.GenerativeModel("gemini-1.5-flash")

# Define the prompt template
prompt_template = """
You are an expert at creating True/False and Multiple Choice questions based on documentation.
Your goal is to prepare students for their test.
For each text chunk below, create the following:

- **True/False questions**: + Each question must be based on key facts or concepts from the text.
                            + The question should be concise and easy to answer.
- **Multiple Choice questions**: + Each question must have four options, one of which is correct. 
                                 + The questions should assess comprehension of important details from the text.

Format the output like this (The answer must be returned in array format):
1. For True/False questions:
    - "question": The question,
    - "options": ["True", "False"],
    - "answer": A boolean representing the correct answer (True or False).
   
2. For Multiple Choice questions:
    - "question": The question,
    - "options": An array of 4 strings representing the choices,
    - "answer": The index number (0-3) of the correct answer in the options array.

Ensure the questions are relevant to the content and concise.

Based on the following passage:
-----------
{text}
-----------

QUESTIONS:
"""

# Initialize PromptTemplate
question_prompt = PromptTemplate(
    template=prompt_template,
    input_variables=["text"]
)

def generate_question_from_chunks(text):
    """
    Generates questions based on the input text chunk.

    Args:
        text (str): The text chunk to generate questions from.

    Returns:
        str: Generated questions in JSON format.
    """
    try:
        # Format the prompt using the input text
        formatted_prompt = question_prompt.format(text=text)
        # Generate questions using the model
        response = model.generate_content(formatted_prompt)

        # Extract the content of the response
        response =response.candidates[0].content.parts[0].text
        # Tìm vị trí của ký tự bắt đầu trong chuỗi
        start_index = response.find("[")
        end_index = response.find("}]")
        # Kiểm tra xem ký tự có tồn tại trong chuỗi không
        if start_index != -1:
            result = response[start_index:end_index-4]
            quiz_json = json.loads(result)
            return quiz_json
    except Exception as e:
        return str(e)

# Export the function for use in app.py
__all__ = ["generate_question_from_chunks"]
input_text = """
HTML is a markup language used for structuring content on the web.

CSS (Cascading Style Sheets) is a style sheet language used to describe the presentation of a document written in HTML or XML (including XML-based languages such as SVG or XHTML). CSS enables developers to control the layout, design, and visual appearance of web pages, including aspects like colors, fonts, spacing, alignment, and animations..
"""

quiz = generate_question_from_chunks(input_text)