import os
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

GPT_MODEL = "gpt-3.5-turbo"
openai_api_key = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=openai_api_key)

pdf_file_path = '/workspaces/autochat-bot/uploads/d440358dars.pdf'
reader = PdfReader(pdf_file_path)
pdf_texts = [page.extract_text().strip() for page in reader.pages if page.extract_text()]
pdf_text = "\n".join(pdf_texts)

model = SentenceTransformer('all-MiniLM-L6-v2')
pdf_embedding = model.encode(pdf_text)

query1 = "Please summarize the key points from the PDF."
retrieved_documents = pdf_text

def rag(query, retrieved_documents, model=GPT_MODEL):
    #information = f"Knowledge Cutoff Date: PASTE HERE DATE FROM {retrieved_documents} *Company Overview:*,*Financial Highlights:*,*Financials Table data overview*,*Management Summary*,*Growth Drivers:*,*Risks:*,*Valuation:*,*Investment Thesis:*,*three different investor views on the stock:*,**Investment Risks:**, **Market Volatility:**,**Regulatory Risks:**, **Global Economic Conditions:** and a swap analysis in sections and bullet points about. Answer the user's question using only this information."

    messages = [
        {
            "role": "system",
            "content": "You are a helpful expert financial research assistant. Your users are asking questions about information contained in an annual report."
        },
        {"role": "user", "content": f"Question: {query}. \n Document: retrieved_documents"}
    ]

    response = client.chat.completions.create(
        model=model,
        messages=messages,
    )
    content = response.choices[0].message.content
    return content

response = rag(query1, retrieved_documents)
print(response)
