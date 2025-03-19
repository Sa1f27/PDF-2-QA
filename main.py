import re
import os
import fitz  # PyMuPDF
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from groq import Groq

def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file."""
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def extract_questions(text):
    """Extract questions from the text.
    Assumes questions start with Q followed by a number and most likely end with ? or before 'ans'
    """
    # Pattern to match questions starting with Q followed by number
    pattern = r'Q\d+\.?\s*([^?]+\??)'
    questions = re.findall(pattern, text)

    # Clean up the questions
    cleaned_questions = []
    for q in questions:
        # Remove any 'ans' or 'Ans' at the end if present
        q = re.split(r'\s*[Aa]ns\s*', q)[0].strip()
        cleaned_questions.append(q)

    return cleaned_questions

def get_llm_answer(question, expertise_level, api_key):
    """Get an answer from the Groq Llama LLM based on expertise level."""
    client = Groq(api_key=api_key)

    # Define prompts for different expertise levels
    if expertise_level == "beginner":
        system_prompt = """You are a helpful assistant with basic knowledge.
        Provide a concise, simple answer that a beginner would understand.
        Keep your answer under 100 words and use simple language."""
    elif expertise_level == "intermediate":
        system_prompt = """You are an assistant with 1-2 years of professional experience.
        Provide a concise but more detailed answer that demonstrates understanding of relevant concepts.
        Keep your answer under 150 words and use appropriate terminology."""
    else:  # advanced
        system_prompt = """You are an advanced expert with 4-5 years of professional experience.
        Provide a concise but sophisticated answer that demonstrates deep understanding.
        Include nuanced insights while keeping your answer under 200 words."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Please answer the following question: {question}"}
    ]

    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        temperature=0.7,
        max_tokens=800
    )

    return completion.choices[0].message.content

def create_enhanced_pdf_with_qa(questions, answers_sets, output_path):
    """Create a nicely formatted PDF with questions and answers at different expertise levels."""
    doc = SimpleDocTemplate(output_path, pagesize=letter)
    styles = getSampleStyleSheet()

    # Create custom styles
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Title'],
        fontSize=18,
        spaceAfter=24
    )

    question_style = ParagraphStyle(
        'QuestionStyle',
        parent=styles['Heading2'],
        fontSize=14,
        spaceBefore=12,
        spaceAfter=12,
        textColor=colors.darkblue
    )

    section_style = ParagraphStyle(
        'SectionStyle',
        parent=styles['Heading3'],
        fontSize=12,
        spaceBefore=6,
        spaceAfter=6,
        textColor=colors.darkslategray
    )

    answer_style = ParagraphStyle(
        'AnswerStyle',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        leftIndent=20,
        spaceAfter=12
    )

    # Create the content
    content = []
    content.append(Paragraph("Questions and Answers by Expertise Level", title_style))

    for i, question in enumerate(questions):
        # Add the question
        content.append(Paragraph(f"Q{i+1}. {question}", question_style))

        # Add answers for each expertise level
        content.append(Paragraph("Beginner's Answer:", section_style))
        content.append(Paragraph(answers_sets[i]["beginner"], answer_style))

        content.append(Paragraph("Intermediate Expert's Answer (1-2 years experience):", section_style))
        content.append(Paragraph(answers_sets[i]["intermediate"], answer_style))

        content.append(Paragraph("Advanced Expert's Answer (4-5 years experience):", section_style))
        content.append(Paragraph(answers_sets[i]["advanced"], answer_style))

        # Add separator between Q&A sets
        content.append(Spacer(1, 24))

    # Build the PDF
    doc.build(content)

def main():
    # Get the API key from environment variable for security
    api_key = "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"
    if not api_key:
        print("Error: GROQ_API_KEY environment variable not set")
        return

    # Input and output file paths
    input_pdf ="/content/SAP Basis questions and answers-JRK-Latest (1).pdf"
    output_pdf = r"output-sap-2.pdf"

    # Extract text from the PDF
    text = extract_text_from_pdf(input_pdf)

    # Extract questions from the text
    questions = extract_questions(text)

    if not questions:
        print("No questions found in the PDF.")
        return

    print(f"Found {len(questions)} questions. Generating answers at different expertise levels...")

    # Get answers from the LLM at different expertise levels
    all_answers = []
    for i, question in enumerate(questions):
        print(f"Processing question {i+1}/{len(questions)}...")
        answers = {
            "beginner": get_llm_answer(question, "beginner", api_key),
            "intermediate": get_llm_answer(question, "intermediate", api_key),
            "advanced": get_llm_answer(question, "advanced", api_key)
        }
        all_answers.append(answers)
        print(f"Completed answers for question {i+1}")

    # Create the output PDF
    create_enhanced_pdf_with_qa(questions, all_answers, output_pdf)

    print(f"Done! Output PDF created at {output_pdf}")

if __name__ == "__main__":
    main()
