import os
from fpdf import FPDF
from textblob import TextBlob
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import uuid
from pathlib import Path
from llm_service import get_llm_response
from datetime import datetime
import re

# Ensure directories exist
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR.parent / "frontend"
REPORTS_DIR = STATIC_DIR / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

def nuclear_clean(text):
    """Most aggressive cleaning - only keeps letters, numbers, spaces, and basic punctuation."""
    if not isinstance(text, str):
        text = str(text)
    
    # Remove all special characters except letters, numbers, spaces, and . , ! ? : ;
    text = re.sub(r'[^a-zA-Z0-9\s.,!?:;\'\"-]', '', text)
    
    # Remove multiple spaces
    text = re.sub(r'\s+', ' ', text)
    
    # Remove placeholders
    text = re.sub(r'Insert\s+Current\s+Date', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Insert\s+[\w\s]+', '', text, flags=re.IGNORECASE)
    
    return text.strip()

def analyze_sentiment(text):
    """Returns a polarity score between -1 (negative) and 1 (positive)."""
    return TextBlob(text).sentiment.polarity

def generate_sentiment_graph(scores, session_id):
    """Generates a line graph of sentiment scores and saves it."""
    plt.figure(figsize=(10, 5))
    plt.plot(scores, marker='o', linestyle='-', color='b')
    plt.title('Conversation Sentiment Analysis')
    plt.xlabel('Message Index')
    plt.ylabel('Sentiment Score (-1 to 1)')
    plt.grid(True)
    
    graph_filename = f"{session_id}_graph.png"
    graph_path = REPORTS_DIR / graph_filename
    plt.savefig(graph_path)
    plt.close()
    return graph_path

async def generate_soap_section(history_text, section_name, section_instructions):
    """Generate one SOAP section with strict formatting."""
    
    system_instruction = f"""You are a licensed clinical psychologist writing the {section_name} section of a medical SOAP note.

CRITICAL INSTRUCTIONS:
- Write at least 5-7 complete sentences based ONLY on the actual conversation provided
- Use ONLY plain text - NO special characters
- DO NOT use asterisks, hashtags, pipes, dashes, or brackets
- DO NOT use bullet points or numbered lists
- Write in prose format only
- DO NOT make up information - only use what's in the conversation

BAD EXAMPLE (DO NOT DO THIS):
**Subjective:** Patient reports...
### Primary Concerns
- Feeling stressed
--- 

GOOD EXAMPLE (DO THIS):
The patient reports experiencing significant psychological distress over the past several weeks. The primary concern expressed was feeling overwhelmed by daily responsibilities. The patient specifically mentioned difficulty sleeping and decreased appetite. There were no reports of suicidal ideation or intent to harm self or others. The patient expressed willingness to engage in treatment.

YOUR TASK:
{section_instructions}

Write your response as plain English prose (5-7 sentences minimum) based on the actual conversation below:"""
    
    user_request = f"Please write the {section_name} section based on this conversation."
    
    try:
        # Pass: history_text, user_request, system_instruction
        response = await get_llm_response(history_text, user_request, system_instruction)
        cleaned = nuclear_clean(response)
        
        # Ensure minimum length
        if len(cleaned) < 50:
            cleaned = f"The patient engaged in a brief therapeutic interaction. {cleaned} Further assessment is recommended."
        
        return cleaned
    except Exception as e:
        print(f"Error generating {section_name}: {e}")
        return f"Unable to generate complete {section_name} assessment due to technical error. Please review full transcript for details."

async def generate_doctor_summary(history_text):
    """Generate all SOAP sections with detailed content."""
    
    # Truncate history
    if len(history_text) > 4000:
        history_text = "...(earlier conversation truncated)...\n" + history_text[-4000:]
    
    sections = {}
    
    sections['subjective'] = await generate_soap_section(
        history_text,
        "SUBJECTIVE",
        "Describe what the patient explicitly reported about their mental health concerns, symptoms, feelings, medical history, and reasons for seeking help. Include their own words when relevant."
    )
    
    sections['objective'] = await generate_soap_section(
        history_text,
        "OBJECTIVE",
        "Describe your clinical observations of the patient's presentation, including mood, affect, speech patterns, thought process, communication style, and any notable behavioral observations during the conversation."
    )
    
    sections['assessment'] = await generate_soap_section(
        history_text,
        "ASSESSMENT",
        "Provide your professional clinical impression and diagnostic considerations based on the conversation. Discuss the severity of symptoms, functional impairment, and any preliminary diagnostic impressions."
    )
    
    sections['plan'] = await generate_soap_section(
        history_text,
        "PLAN",
        "Outline specific recommendations for the treating physician, including suggested assessments, therapeutic interventions, medication considerations, referrals, safety planning, and follow-up recommendations."
    )
    
    return sections

class PDFReport(FPDF):
    def __init__(self):
        super().__init__()
        self.report_datetime = datetime.now().strftime("%B %d, %Y at %I:%M %p")
    
    def header(self):
        self.set_font('Arial', 'B', 18)
        self.cell(0, 12, 'Mental Health Consultation Report', 0, 1, 'C')
        self.set_font('Arial', '', 10)
        self.cell(0, 6, f'Report Generated: {self.report_datetime}', 0, 1, 'C')
        self.ln(3)
        self.set_line_width(0.5)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(8)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

async def create_pdf_report(session_id, history):
    """Generates a professional PDF report."""
    try:
        pdf = PDFReport()
        pdf.add_page()

        # 1. Process conversation data
        sentiment_scores = []
        conversation_text = ""
        
        current = history.head
        while current:
            role = current.role.capitalize()
            content = current.content
            content = content.encode('latin-1', 'replace').decode('latin-1')
            conversation_text += f"{role}: {content}\n"
            
            if role == "User":
                score = analyze_sentiment(content)
                sentiment_scores.append(score)
            
            current = current.next

        # 2. Generate sentiment graph
        if not sentiment_scores:
            sentiment_scores = [0]
        graph_path = generate_sentiment_graph(sentiment_scores, session_id)

        # 3. Generate clinical summary
        summary_sections = await generate_doctor_summary(conversation_text)

        # 4. Build PDF - Clinical Summary
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, "Clinical Summary (SOAP Format)", 0, 1)
        pdf.ln(3)
        
        soap_sections = [
            ("SUBJECTIVE", summary_sections.get('subjective', 'N/A')),
            ("OBJECTIVE", summary_sections.get('objective', 'N/A')),
            ("ASSESSMENT", summary_sections.get('assessment', 'N/A')),
            ("PLAN", summary_sections.get('plan', 'N/A'))
        ]
        
        for label, content in soap_sections:
            # Clean content
            content = nuclear_clean(str(content))
            content = content.encode('latin-1', 'replace').decode('latin-1')
            
            # Render section
            pdf.set_font('Arial', 'B', 12)
            pdf.set_fill_color(240, 240, 240)
            pdf.cell(0, 8, label, 0, 1, 'L', 1)
            pdf.ln(2)
            
            pdf.set_font('Arial', '', 11)
            pdf.multi_cell(0, 6, content)
            pdf.ln(5)
        
        # 5. Sentiment Analysis
        pdf.ln(5)
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, "Sentiment Analysis", 0, 1)
        pdf.ln(2)
        try:
            pdf.image(str(graph_path), x=10, w=190)
        except:
            pdf.set_font('Arial', '', 11)
            pdf.cell(0, 6, "Graph unavailable", 0, 1)
        
        # 6. Conversation Transcript
        pdf.add_page()
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, "Conversation Transcript", 0, 1)
        pdf.ln(5)
        
        current = history.head
        while current:
            role = current.role.capitalize()
            content = current.content
            content = content.encode('latin-1', 'replace').decode('latin-1')

            if role == "User":
                pdf.set_text_color(0, 70, 180)
                pdf.set_font("Arial", 'B', 10)
                pdf.cell(0, 5, "Patient:", 0, 1)
            else:
                pdf.set_text_color(0, 120, 80)
                pdf.set_font("Arial", 'B', 10)
                pdf.cell(0, 5, "Therapist (AI):", 0, 1)
            
            pdf.set_text_color(0, 0, 0)
            pdf.set_font("Arial", '', 10)
            pdf.multi_cell(0, 5, content)
            pdf.ln(3)
            current = current.next

        # Save PDF
        report_filename = f"report_{session_id}.pdf"
        report_path = REPORTS_DIR / report_filename
        pdf.output(str(report_path))
        
        return f"/static/reports/{report_filename}"

    except Exception as e:
        print(f"Report Error: {e}")
        raise e
