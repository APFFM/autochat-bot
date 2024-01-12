from dotenv import load_dotenv
load_dotenv()
from flask import Flask, render_template, jsonify, request, session
from flask_session import Session
from werkzeug.utils import secure_filename
from flask_cors import CORS
from openai import OpenAI

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
import os
from flask import Flask, render_template,jsonify,request
from flask_cors import CORS
import requests,openai,os
from dotenv.main import load_dotenv
from langchain.llms import OpenAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain
from langchain.memory import ConversationSummaryBufferMemory
llm = OpenAI(openai_api_key=os.getenv('OPENAI_API_KEY'))
memory = ConversationSummaryBufferMemory(llm=llm, max_token_limit=100)
app = Flask(__name__)
CORS(app)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['SESSION_TYPE'] = 'filesystem'
app.secret_key = os.urandom(24)  # You should set a secret key for session management
Session(app)

ALLOWED_EXTENSIONS = {'pdf'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
 
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify(error="No file part"), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify(error="No selected file"), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        try:
            uploaded_file = client.files.create(file=open(file_path, 'rb'), purpose='assistants')
            session['file_id'] = uploaded_file.id  # Save the file id in the session
            return jsonify({"response": True, "file_id": uploaded_file.id})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

@app.route('/data', methods=['POST'])
def get_data():
    data = request.get_json()
    user_input = data['data']
    file_id = session.get('file_id')  # Retrieve the file id from session

    try:
        # Add the file to the assistant
        assistant = llm.beta.assistants.create(
            instructions="You are a knowledge support chatbot. Use your knowledge base to best respond to customer queries.",
            model="gpt-4-1106-preview",
            tools=[{"type": "retrieval"}],
            file_ids=[file.id]
        )
        # Create a thread for the conversation
        thread = openai.Thread.create()

        # Create a message in the thread
        message = openai.Message.create(
            thread_id=thread.id,
            role="user",
            content=user_input,
            file_ids=[file_id]
        )

        # Assuming we're immediately getting the response (synchronous interaction)
        # If the interaction is asynchronous, you would need to poll for the response
        assistant_response = openai.Message.create(
            thread_id=thread.id,
            role="assistant",
            content="Explain and summarize the pdf in your context",
            file_ids=[file_id]
        )

        #adding conversation
        conversation = ConversationChain(llm=llm,memory=memory)

        # Extract the assistant's response message
        output = assistant_response['choices'][0]['message']['content']
        memory.save_context({"input": user_input}, {"output": output})
        return jsonify({"response":True,"message":output})
    except Exception as e:
        print(e)
        error_message = f'Error: {str(e)}'
        return jsonify({"message":error_message,"response":False})

if __name__ == '__main__':
    app.run(debug=True)