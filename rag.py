from flask import Flask, request, jsonify, session
from werkzeug.utils import secure_filename
import openai
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Assuming OPENAI_API_KEY is set in your environment variables
openai.api_key = os.getenv('OPENAI_API_KEY')

@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files['file']
    filename = secure_filename(file.filename)
    file_path = os.path.join('uploads', filename)
    file.save(file_path)

    uploaded_file = openai.File.create(file=open(file_path, 'rb'), purpose='assistants')
    session['file_id'] = uploaded_file.id
    return jsonify({"file_id": uploaded_file.id})

@app.route('/create-assistant', methods=['POST'])
def create_assistant():
    file_id = session.get('file_id')
    if not file_id:
        return jsonify({"error": "File ID not found in session"}), 400

    assistant = openai.Assistant.create(
        model="gpt-4-1106-preview",
        tools=[{"type": "retrieval"}],
        file_ids=[file_id]
    )
    session['assistant_id'] = assistant.id
    return jsonify({"assistant_id": assistant.id})

@app.route('/ask', methods=['POST'])
def ask():
    data = request.get_json()
    user_query = data.get('query')
    assistant_id = session.get('assistant_id')
    file_id = session.get('file_id')

    if not assistant_id:
        return jsonify({"error": "Assistant ID not found in session"}), 400
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
