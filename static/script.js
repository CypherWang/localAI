let currentSessionId = 1;

document.getElementById('send-button').addEventListener('click', sendMessage);
document.getElementById('user-input').addEventListener('keydown', function (event) {
    if (event.key === 'Enter') {
        sendMessage();
    }
});

async function sendMessage() {
    const userInput = document.getElementById('user-input').value;
    if (!userInput) return;

    appendMessage(userInput, 'user', '/static/images/user-avatar.png');
    document.getElementById('user-input').value = '';

    const response = await fetch('/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            message: userInput,
            session_id: currentSessionId
        })
    });

    const data = await response.json();
    const assistantMessage = data.reply;
    appendMessage(assistantMessage, 'assistant', '/static/images/assistant-avatar.png');
}

function appendMessage(message, role, avatar) {
    const messageContainer = document.createElement('div');
    messageContainer.className = `message-container ${role}`;

    const messageElement = document.createElement('div');
    messageElement.className = 'message';
    messageElement.textContent = message;

    const avatarElement = document.createElement('img');
    avatarElement.className = 'avatar';
    avatarElement.src = avatar;

    messageContainer.appendChild(avatarElement);
    messageContainer.appendChild(messageElement);
    document.getElementById('chat').appendChild(messageContainer);
    document.getElementById('chat').scrollTop = document.getElementById('chat').scrollHeight;
}

async function loadSessions() {
    const response = await fetch('/sessions');
    const sessions = await response.json();
    const sessionList = document.getElementById('session-list');
    sessionList.innerHTML = '';

    sessions.forEach(sessionId => {
        const li = document.createElement('li');
        li.textContent = `Session ${sessionId}`;
        li.addEventListener('click', () => loadSession(sessionId));
        sessionList.appendChild(li);
    });
}

async function loadSession(sessionId) {
    currentSessionId = sessionId;
    const response = await fetch(`/history/${sessionId}`);
    const history = await response.json();
    const chat = document.getElementById('chat');
    chat.innerHTML = '';

    history.forEach(({ role, content }) => {
        const avatar = role === 'user' ? '/static/images/user-avatar.png' : '/static/images/assistant-avatar.png';
        appendMessage(content, role, avatar);
    });
}

// 加载现有会话列表
loadSessions();
