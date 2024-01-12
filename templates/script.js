
<script>
// Scroll the chat to the bottom
function scrollToBottom() {
    var div = document.getElementById("upperid");
    div.scrollTop = div.scrollHeight;
  }
  
  // Function to display messages in the chat
  function displayMessage(message, sender) {
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message');
    const senderDiv = document.createElement('div');
    senderDiv.classList.add(sender === 'assistant' ? 'appmessagediv' : 'usermessagediv');
  
    const messageContent = document.createElement('div');
    messageContent.classList.add('appmessage');
    if (sender === 'user') {
      messageContent.classList.add('usermessage');
    } else if (sender === 'error') {
      messageContent.style.border = '1px solid red';
    }
  
    messageContent.textContent = message;
    senderDiv.appendChild(messageContent);
    messageDiv.appendChild(senderDiv);
    document.getElementById('upperid').appendChild(messageDiv);
  
    scrollToBottom();
  }
  
  // Function to display errors in the chat
  function displayError(message) {
    displayMessage(message, 'error');
  }
  
  // Function to handle both text messages and file uploads
  async function processInput(userInput, fileInput) {
    // Disable input and button while processing
    document.getElementById('sendbtn').disabled = true;
    document.getElementById('userinput').disabled = true;
  
    let formData = new FormData();
    formData.append('data', userInput);
  
    // If there is a file to upload, append it to the form data
    if (fileInput && fileInput.files.length > 0) {
      formData.append('file', fileInput.files[0]);
    }
  
    // Send request to the server
    const response = await fetch('/data', {
      method: 'POST',
      body: formData
    });
  
    // Handle the response from the server
    const json = await response.json();
  
    // Re-enable input and button after processing
    document.getElementById('sendbtn').disabled = false;
    document.getElementById('userinput').disabled = false;
  
    // Display the message or error
    if (json.response) {
      displayMessage(json.message, 'assistant');
    } else {
      displayError(json.message);
    }
  
    scrollToBottom();
  }
  
  // Event listeners for form submission and file upload
  document.getElementById("userinputform").addEventListener("submit", function(event) {
    event.preventDefault();
    const userInputField = document.getElementById('userinput');
    const userInput = userInputField.value;
    userInputField.value = ''; // Clear the input field
  
    displayMessage(userInput, 'user'); // Display the user's message immediately in the chat
    processInput(userInput, null); // Process input without a file
  });
  
  document.getElementById('file-upload-form').addEventListener('submit', function(event) {
    event.preventDefault();
    const fileInput = document.getElementById('fileinput'); // Make sure this ID matches your file input ID
  
    // Display a placeholder message or handle file upload display logic
    displayMessage("Uploading file...", 'user');
  
    processInput("Processing uploaded file...", fileInput); // Process input with a file
  });
  
  // Initial call to scrollToBottom to ensure the chat starts at the bottom
  scrollToBottom(); 
  </script>