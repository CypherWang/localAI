let currentSessionId = null;
let currentSessionName = null;
let currentPage = 1;
const messagesPerPage = 10;

document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('send-button').addEventListener('click', sendMessage);
    document.getElementById('user-input').addEventListener('keydown', handleInputKeydown);
    document.getElementById('new-session-button').addEventListener('click', createSession);
    document.getElementById('session-list').addEventListener('click', handleSessionClick);
    document.getElementById('insert-weather-button').addEventListener('click', insertWeatherTag);

    loadSessions();
});

function handleInputKeydown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    } else {
        autoResizeTextarea();
    }
}

function autoResizeTextarea() {
    const textarea = document.getElementById('user-input');
    textarea.style.height = 'auto';
    textarea.style.height = (textarea.scrollHeight) + 'px';
}

async function sendMessage() {
    const userInput = document.getElementById('user-input').value.trim();
    if (!userInput || !currentSessionId) return;

    appendMessage(userInput, 'user', '/static/images/user-avatar.png');
    document.getElementById('user-input').value = '';
    autoResizeTextarea();

    try {
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

        if (!response.ok) throw new Error('Network response was not ok');

        const data = await response.json();
        appendMessage(data.reply, 'assistant', '/static/images/assistant-avatar.png');
    } catch (error) {
        console.error('Error sending message:', error);
        appendMessage('Error sending message. Please try again.', 'error');
    }
}

function appendMessage(message, role, avatar) {
    const messageContainer = document.createElement('div');
    messageContainer.className = `message-container ${role}`;

    const messageElement = document.createElement('div');
    messageElement.className = 'message';

    // 将 [WEATHER:xxx] 标记转换为斜体文本
    message = message.replace(/\[WEATHER:(.*?)\]/g, '<em>天气查询：$1</em>');
    messageElement.innerHTML = message;

    const avatarElement = document.createElement('img');
    avatarElement.className = 'avatar';
    avatarElement.src = avatar;

    if (role === 'user') {
        messageContainer.appendChild(messageElement);
        messageContainer.appendChild(avatarElement);
    } else {
        messageContainer.appendChild(avatarElement);
        messageContainer.appendChild(messageElement);
    }

    document.getElementById('chat').appendChild(messageContainer);
    document.getElementById('chat').scrollTop = document.getElementById('chat').scrollHeight;
}

// 添加一个新的辅助函数来插入天气查询标记
function insertWeatherTag() {
    const userInput = document.getElementById('user-input');
    const locationId = prompt("请输入城市的 LocationID（例如：北京为101010100）：");
    if (locationId) {
        const weatherTag = `[WEATHER:${locationId}]`;
        const cursorPos = userInput.selectionStart;
        const textBefore = userInput.value.substring(0, cursorPos);
        const textAfter = userInput.value.substring(cursorPos);
        userInput.value = textBefore + weatherTag + textAfter;
        userInput.focus();
        userInput.selectionStart = userInput.selectionEnd = cursorPos + weatherTag.length;
    }
}

async function loadSessions() {
    try {
        const response = await fetch('/sessions');
        if (!response.ok) throw new Error('Network response was not ok');
        const sessions = await response.json();
        renderSessions(sessions);
    } catch (error) {
        console.error('Error loading sessions:', error);
        document.getElementById('session-list').innerHTML = '<li>Error loading sessions. Please refresh.</li>';
    }
}

function renderSessions(sessions) {
    const sessionList = document.getElementById('session-list');
    sessionList.innerHTML = '';

    sessions.forEach(session => {
        const li = document.createElement('li');
        li.innerHTML = `
            <span data-session-id="${session.session_id}">${session.session_name}</span>
            <button class="rename-btn">Rename</button>
            <button class="delete-btn">Delete</button>
        `;
        sessionList.appendChild(li);
    });
}

function handleSessionClick(event) {
    const target = event.target;
    if (target.tagName === 'SPAN') {
        loadSession(target.dataset.sessionId, target.textContent);
    } else if (target.classList.contains('rename-btn')) {
        const span = target.previousElementSibling;
        renameSession(span.dataset.sessionId, span);
    } else if (target.classList.contains('delete-btn')) {
        const span = target.previousElementSibling.previousElementSibling;
        deleteSession(span.dataset.sessionId);
    }
}

async function loadSession(sessionId, sessionName) {
    if (sessionId === currentSessionId) return;

    currentSessionId = sessionId;
    currentSessionName = sessionName;
    document.getElementById('session-title').textContent = sessionName;
    document.getElementById('chat').innerHTML = '<div class="loading">Loading messages...</div>';
    currentPage = 1;
    await loadMessages();
}

async function loadMessages() {
    if (!currentSessionId) return;

    try {
        const response = await fetch(`/history/${currentSessionId}`);
        if (!response.ok) throw new Error('Network response was not ok');
        const history = await response.json();
        const chat = document.getElementById('chat');

        chat.innerHTML = '';

        if (history.length === 0) {
            chat.innerHTML = '<div class="no-messages">No messages in this session yet.</div>';
        } else {
            history.forEach(({ role, content }) => {
                const avatar = role === 'user' ? '/static/images/user-avatar.png' : '/static/images/assistant-avatar.png';
                appendMessage(content, role, avatar);
            });
        }

        // 移除分页相关代码
        document.getElementById('pagination').innerHTML = '';
    } catch (error) {
        console.error('Error loading messages:', error);
        document.getElementById('chat').innerHTML = '<div class="error">Error loading messages. Please try again.</div>';
    }
}

// 移除 updatePagination 函数

// ... [保留其他函数不变] ...
function updatePagination() {
    const pagination = document.getElementById('pagination');
    pagination.innerHTML = '';

    const prevPage = document.createElement('button');
    prevPage.textContent = 'Previous';
    prevPage.disabled = currentPage === 1;
    prevPage.addEventListener('click', () => {
        if (currentPage > 1) {
            currentPage--;
            loadMessages();
        }
    });
    pagination.appendChild(prevPage);

    const nextPage = document.createElement('button');
    nextPage.textContent = 'Next';
    nextPage.addEventListener('click', () => {
        currentPage++;
        loadMessages();
    });
    pagination.appendChild(nextPage);
}

async function createSession() {
    try {
        const response = await fetch('/session', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                session_name: 'New Session'
            })
        });

        if (!response.ok) throw new Error('Network response was not ok');

        const newSession = await response.json();
        await loadSessions();
        loadSession(newSession.session_id, newSession.session_name);
    } catch (error) {
        console.error('Error creating session:', error);
        alert('Error creating new session. Please try again.');
    }
}

async function renameSession(sessionId, spanElement) {
    const newName = prompt("Enter new session name:", spanElement.textContent);
    if (!newName) return;

    try {
        const response = await fetch(`/session/${sessionId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                session_name: newName
            })
        });

        if (!response.ok) throw new Error('Network response was not ok');

        spanElement.textContent = newName;

        if (sessionId === currentSessionId) {
            currentSessionName = newName;
            document.getElementById('session-title').textContent = newName;
        }
    } catch (error) {
        console.error('Error renaming session:', error);
        alert('Error renaming session. Please try again.');
    }
}

async function deleteSession(sessionId) {
    const confirmed = confirm("Are you sure you want to delete this session?");
    if (!confirmed) return;

    try {
        const response = await fetch(`/session/${sessionId}`, {
            method: 'DELETE',
        });

        if (!response.ok) throw new Error('Network response was not ok');

        await loadSessions();
        if (sessionId === currentSessionId) {
            currentSessionId = null;
            currentSessionName = null;
            document.getElementById('session-title').textContent = "Select a session";
            document.getElementById('chat').innerHTML = '';
        }
    } catch (error) {
        console.error('Error deleting session:', error);
        alert('Error deleting session. Please try again.');
    }
}