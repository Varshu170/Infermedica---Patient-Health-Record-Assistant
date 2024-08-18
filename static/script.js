document.addEventListener('DOMContentLoaded', function () {
    const chatBox = document.getElementById('chat-box');
    const chatInput = document.getElementById('chat-input');
    const sendBtn = document.getElementById('send-btn');
    const micBtn = document.getElementById('mic-btn');
    let awaitingPatientID = false;
    let storedQuestion = '';

    function addMessage(content, sender) {
        const message = document.createElement('div');
        message.classList.add('message', sender);

        if (sender === 'bot') {
            const textContainer = document.createElement('div');
            textContainer.innerText = content;

            const speakerIcon = document.createElement('span');
            speakerIcon.classList.add('speaker-icon');
            speakerIcon.innerHTML = '🔊'; // Update to your speaker icon
            speakerIcon.onclick = function () {
                speakText(content);
            };

            message.appendChild(textContainer);
            message.appendChild(speakerIcon);
        } else {
            message.innerText = content;
        }

        chatBox.appendChild(message);
        scrollToBottom();
    }

    function speakText(text) {
        const speech = new SpeechSynthesisUtterance(text);
        speech.volume = 1;
        speech.rate = 1;
        speech.pitch = 1;
        window.speechSynthesis.speak(speech);
    }

    function scrollToBottom() {
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    function sendQuestion(question, patientID = null) {
        const body = patientID ? { question: storedQuestion, patient_id: patientID } : { question: question };
        fetch('/ask', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(body),
        })
        .then(response => response.json())
        .then(data => {
            if (data.response === 'Multiple patients found. Please provide the patient ID.') {
                awaitingPatientID = true;
                storedQuestion = question;
            }
            addMessage(data.response, 'bot');
        });
    }

    sendBtn.addEventListener('click', function () {
        const input = chatInput.value.trim();
        if (input) {
            addMessage(input, 'user');
            chatInput.value = '';
            if (awaitingPatientID) {
                sendQuestion(storedQuestion, input);
                awaitingPatientID = false;
                storedQuestion = '';
            } else {
                sendQuestion(input);
            }
        }
    });

    chatInput.addEventListener('keypress', function (e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            sendBtn.click();
        }
    });

    micBtn.addEventListener('click', function () {
        recordVoice();
    });

    function recordVoice() {
        const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
        recognition.lang = 'en-US';
        recognition.interimResults = false;
        recognition.maxAlternatives = 1;

        recognition.start();

        recognition.onresult = function (event) {
            const transcript = event.results[0][0].transcript;
            chatInput.value = transcript;
        };

        recognition.onerror = function (event) {
            console.error('Speech recognition error', event.error);
            addMessage("Sorry, I couldn't hear you. Please try again.", 'bot');
        };
    }
});