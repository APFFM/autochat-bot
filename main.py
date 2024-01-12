import os
from flask import Flask, render_template, jsonify, request, session
from flask_session import Session
from flask_cors import CORS
import openai
from dotenv import load_dotenv
from langchain.llms import OpenAI
from langchain.memory import ConversationSummaryBufferMemory
from langchain.chains import ConversationChain
from werkzeug.utils import secure_filename

# Load environment variables
load_dotenv()

# Flask app setup
app = Flask(__name__)
CORS(app)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['SESSION_TYPE'] = 'filesystem'
app.secret_key = os.urandom(24)
Session(app)

# OpenAI API setup
openai_api_key = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=openai_api_key)
memory = ConversationSummaryBufferMemory(llm=client, max_token_limit=100)

# Define allowed file extension
ALLOWED_EXTENSIONS = {'pdf'}

# Helper function to check file extension
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
            # Process the file with OpenAI API
            uploaded_file = client.files.create(file=open(file_path, 'rb'), purpose='assitants')
            session['file_id'] = uploaded_file.id  # Save the file id in the session
            return jsonify({"response": True, "file_id": uploaded_file.id})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    
@app.route('/ask', methods=['POST'])
def ask():
    # Get the user query from the incoming JSON data
    data = request.get_json()
    user_query = data.get('query')

    # Retrieve the assistant_id stored in the session
    assistant_id = session.get('assistant_id')
    if not assistant_id:
        return jsonify({"error": "Assistant ID not found in session"}), 400

    # Retrieve the file_id stored in the session
    file_id = session.get('file_id')
    if not file_id:
        return jsonify({"error": "File ID not found in session"}), 400

    try:
        # Create a thread for this assistant session
        thread = openai.Thread.create(assistant_id=assistant_id)

        # Send the user's query to the assistant
        message_response = openai.Message.create(
            thread_id=thread.id,
            role="user",
            content=user_query,
            file_ids=[file_id]
        )

        # Retrieve the assistant's response from the message response
        assistant_response = message_response.get('data')

        # If the response is successful, extract the content from the response
        if assistant_response:
            response_content = assistant_response['choices'][0]['message']['content']
            return jsonify({"response": response_content})
        else:
            return jsonify({"error": "Failed to get a valid response from the assistant"}), 500
    except Exception as e:
        # If an error occurs, return the error message
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
