// API 基础路径
const API_BASE = 'http://127.0.0.1:8000/api/user';

// 全局状态管理
const state = {
    token: localStorage.getItem('token') || null,
    currentSessionId: null,
    username: localStorage.getItem('username') || null,
    isLoading: false
};

// 页面初始化
document.addEventListener('DOMContentLoaded', () => {
    if (state.token) {
        showChatPage();
        loadUserInfo();
        loadSessionList();
        initNewSession();
    } else {
        showAuthPage();
    }
    
    initEventListeners();
});

// 初始化事件监听
function initEventListeners() {
    // 登录注册切换
    document.getElementById('show-register').addEventListener('click', (e) => {
        e.preventDefault();
        document.getElementById('login-form').style.display = 'none';
        document.getElementById('register-form').style.display = 'block';
    });

    document.getElementById('show-login').addEventListener('click', (e) => {
        e.preventDefault();
        document.getElementById('register-form').style.display = 'none';
        document.getElementById('login-form').style.display = 'block';
    });

    // 登录
    document.getElementById('login-btn').addEventListener('click', handleLogin);
    document.getElementById('login-password').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleLogin();
    });

    // 注册
    document.getElementById('register-btn').addEventListener('click', handleRegister);
    
    // 退出登录
    document.getElementById('logout-btn').addEventListener('click', handleLogout);

    // 新建对话
    document.getElementById('new-chat-btn').addEventListener('click', initNewSession);

    // 发送消息
    document.getElementById('send-btn').addEventListener('click', handleSendMessage);
    
    // 输入框事件
    const messageInput = document.getElementById('message-input');
    messageInput.addEventListener('input', handleInputChange);
    messageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    });
}

// 登录处理
async function handleLogin() {
    const username = document.getElementById('login-username').value.trim();
    const password = document.getElementById('login-password').value.trim();

    if (!username || !password) {
        alert('请填写用户名和密码');
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, password })
        });

        const token = await response.text();
        
        if (response.ok) {
            state.token = token.replace(/"/g, '');
            state.username = username;
            localStorage.setItem('token', state.token);
            localStorage.setItem('username', username);
            
            showChatPage();
            loadUserInfo();
            loadSessionList();
            initNewSession();
        } else {
            alert('登录失败，请检查用户名和密码');
        }
    } catch (error) {
        console.error('登录错误:', error);
        alert('登录失败，请稍后重试');
    }
}

// 注册处理
async function handleRegister() {
    const username = document.getElementById('register-username').value.trim();
    const password = document.getElementById('register-password').value.trim();
    const confirm = document.getElementById('register-confirm').value.trim();

    if (!username || !password || !confirm) {
        alert('请填写完整信息');
        return;
    }

    if (password !== confirm) {
        alert('两次密码不一致');
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, password })
        });

        const data = await response.json();

        if (response.ok && data.code === 200) {
            state.token = data.data.token;
            state.username = username;
            localStorage.setItem('token', state.token);
            localStorage.setItem('username', username);
            
            alert('注册成功！');
            showChatPage();
            loadUserInfo();
            initNewSession();
        } else {
            alert(data.detail || '注册失败');
        }
    } catch (error) {
        console.error('注册错误:', error);
        alert('注册失败，请稍后重试');
    }
}

// 退出登录
function handleLogout() {
    if (confirm('确定要退出登录吗？')) {
        state.token = null;
        state.currentSessionId = null;
        state.username = null;
        localStorage.clear();
        showAuthPage();
        clearMessages();
    }
}

// 加载用户信息
async function loadUserInfo() {
    try {
        const response = await fetch(`${API_BASE}/info`, {
            headers: {
                'Authorization': state.token
            }
        });

        if (response.ok) {
            const data = await response.json();
            const user = data.data;
            document.getElementById('user-name').textContent = user.username;
            document.getElementById('user-avatar').textContent = user.username.charAt(0).toUpperCase();
        }
    } catch (error) {
        console.error('加载用户信息失败:', error);
    }
}

// 加载会话列表
async function loadSessionList() {
    try {
        const response = await fetch(`${API_BASE}/session_id_list`, {
            headers: {
                'Authorization': state.token
            }
        });

        if (response.ok) {
            const data = await response.json();
            const sessionList = document.getElementById('session-list');
            sessionList.innerHTML = '';

            if (data.code === 200 && data.data.length > 0) {
                data.data.forEach(sessionId => {
                    const sessionItem = createSessionItem(sessionId);
                    sessionList.appendChild(sessionItem);
                });
            }
        }
    } catch (error) {
        console.error('加载会话列表失败:', error);
    }
}

// 创建会话列表项
function createSessionItem(sessionId) {
    const div = document.createElement('div');
    div.className = 'session-item';
    div.innerHTML = `
        <div>
            <div class="session-title">会话 ${String(sessionId).substring(0, 8)}</div>
        </div>
    `;
    
    div.addEventListener('click', () => {
        state.currentSessionId = sessionId;
        loadChatHistory(sessionId);
        
        // 更新选中状态
        document.querySelectorAll('.session-item').forEach(item => {
            item.classList.remove('active');
        });
        div.classList.add('active');
    });

    return div;
}

// 初始化新会话
function initNewSession() {
    state.currentSessionId = generateSessionId();
    document.getElementById('current-session-title').textContent = '新对话';
    clearMessages();
    showWelcomeMessage();
    
    // 清除选中状态
    document.querySelectorAll('.session-item').forEach(item => {
        item.classList.remove('active');
    });
}

// 生成会话ID (转换为整数时间戳)
function generateSessionId() {
    return Date.now();
}

// 加载聊天历史
async function loadChatHistory(sessionId) {
    clearMessages();
    showLoadingMessage();

    try {
        const response = await fetch(`${API_BASE}/history?session_id=${sessionId}`, {
            headers: {
                'Authorization': state.token
            }
        });

        if (response.ok) {
            const data = await response.json();
            clearMessages();

            if (data.code === 200 && data.data.length > 0) {
                data.data.forEach(msg => {
                    addMessage(msg.content, msg.role === 'user' ? 'user' : 'ai');
                });
                document.getElementById('current-session-title').textContent = `会话 ${String(sessionId).substring(0, 8)}`;
            } else {
                showWelcomeMessage();
            }
        }
    } catch (error) {
        console.error('加载历史记录失败:', error);
        clearMessages();
        showWelcomeMessage();
    }
}

// 发送消息
async function handleSendMessage() {
    const input = document.getElementById('message-input');
    const message = input.value.trim();

    if (!message || state.isLoading) return;

    const ragEnabled = document.getElementById('rag-option').checked;
    const tavilyEnabled = document.getElementById('tavily-option').checked;

    // 添加用户消息
    addMessage(message, 'user');
    input.value = '';
    input.style.height = 'auto';
    updateSendButton();

    // 显示加载状态
    state.isLoading = true;
    showLoadingMessage();

    try {
        const url = `${API_BASE}/chat?session_id=${state.currentSessionId}&query=${encodeURIComponent(message)}&rag_true=${ragEnabled}&tavily_true=${tavilyEnabled}`;
        
        const response = await fetch(url, {
            headers: {
                'Authorization': state.token
            }
        });

        removeLoadingMessage();

        if (response.ok) {
            const data = await response.json();
            if (data.code === 200) {
                // 伪流式输出
                await streamMessage(data.data.content, 'ai');
                
                // 更新会话列表
                loadSessionList();
            } else {
                addMessage('抱歉，发生了错误，请重试', 'ai');
            }
        } else {
            addMessage('抱歉，请求失败，请重试', 'ai');
        }
    } catch (error) {
        console.error('发送消息失败:', error);
        removeLoadingMessage();
        addMessage('网络错误，请检查连接后重试', 'ai');
    } finally {
        state.isLoading = false;
    }
}

// 添加消息到界面
function addMessage(content, type) {
    const container = document.getElementById('messages-container');
    
    // 移除欢迎消息
    const welcome = container.querySelector('.welcome-message');
    if (welcome) welcome.remove();

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    
    const avatar = type === 'user' ? state.username.charAt(0).toUpperCase() : 'AI';
    
    messageDiv.innerHTML = `
        <div class="message-avatar">${avatar}</div>
        <div class="message-content">${escapeHtml(content)}</div>
    `;

    container.appendChild(messageDiv);
    container.scrollTop = container.scrollHeight;
    
    return messageDiv;
}

// 伪流式输出消息
async function streamMessage(content, type) {
    const container = document.getElementById('messages-container');
    
    // 移除欢迎消息
    const welcome = container.querySelector('.welcome-message');
    if (welcome) welcome.remove();

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    
    const avatar = type === 'user' ? state.username.charAt(0).toUpperCase() : 'AI';
    
    messageDiv.innerHTML = `
        <div class="message-avatar">${avatar}</div>
        <div class="message-content"></div>
    `;

    container.appendChild(messageDiv);
    const contentDiv = messageDiv.querySelector('.message-content');
    
    // 逐字显示
    const text = escapeHtml(content);
    let index = 0;
    const speed = 20; // 每个字符显示间隔(毫秒)
    
    while (index < text.length) {
        contentDiv.textContent += text[index];
        index++;
        container.scrollTop = container.scrollHeight;
        await new Promise(resolve => setTimeout(resolve, speed));
    }
}

// 显示加载动画
function showLoadingMessage() {
    const container = document.getElementById('messages-container');
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'message ai loading';
    loadingDiv.id = 'loading-message';
    
    loadingDiv.innerHTML = `
        <div class="message-avatar">AI</div>
        <div class="message-content">
            <div class="dot"></div>
            <div class="dot"></div>
            <div class="dot"></div>
        </div>
    `;

    container.appendChild(loadingDiv);
    container.scrollTop = container.scrollHeight;
}

// 移除加载动画
function removeLoadingMessage() {
    const loading = document.getElementById('loading-message');
    if (loading) loading.remove();
}

// 显示欢迎消息
function showWelcomeMessage() {
    const container = document.getElementById('messages-container');
    container.innerHTML = `
        <div class="welcome-message">
            <div class="welcome-icon">
                <svg width="64" height="64" viewBox="0 0 64 64" fill="none">
                    <circle cx="32" cy="32" r="28" fill="#f0f2f5"/>
                    <circle cx="32" cy="32" r="20" fill="#3370ff"/>
                    <path d="M32 20L24 34H32L32 44L40 30H32L32 20Z" fill="white"/>
                </svg>
            </div>
            <h2>你好，我是 AI 助手</h2>
            <p>我可以回答问题、提供建议，还可以搜索互联网获取最新信息</p>
        </div>
    `;
}

// 清空消息
function clearMessages() {
    document.getElementById('messages-container').innerHTML = '';
}

// 输入框变化处理
function handleInputChange(e) {
    const input = e.target;
    input.style.height = 'auto';
    input.style.height = Math.min(input.scrollHeight, 120) + 'px';
    updateSendButton();
}

// 更新发送按钮状态
function updateSendButton() {
    const input = document.getElementById('message-input');
    const btn = document.getElementById('send-btn');
    btn.disabled = !input.value.trim() || state.isLoading;
}

// 页面切换
function showAuthPage() {
    document.getElementById('auth-page').style.display = 'flex';
    document.getElementById('chat-page').style.display = 'none';
}

function showChatPage() {
    document.getElementById('auth-page').style.display = 'none';
    document.getElementById('chat-page').style.display = 'flex';
}

// HTML 转义
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 监听窗口关闭前事件（清理会话ID）
window.addEventListener('beforeunload', () => {
    // 窗口关闭时，当前会话ID会被清除，下次打开是新会话
    // 注意：这里不清除 token，用户下次打开仍然保持登录状态
});
