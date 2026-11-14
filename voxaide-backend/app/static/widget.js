/**
 * VoxAide Embeddable AI Voice & Chat Support Widget (2026 Edition)
 * Zero external dependencies. Works on Shopify, WordPress, Webflow, React, HTML.
 */
(function () {
  if (window.VoxaideWidgetLoaded) return;
  window.VoxaideWidgetLoaded = true;

  // 1. Detect script attributes
  var currentScript = document.currentScript || (function() {
    var scripts = document.getElementsByTagName('script');
    for (var i = scripts.length - 1; i >= 0; i--) {
      if (scripts[i].src && scripts[i].src.indexOf('widget.js') !== -1) return scripts[i];
    }
    return null;
  })();

  var companyId = (currentScript && currentScript.getAttribute('data-company-id')) || 'demo_company';
  var agentId = (currentScript && currentScript.getAttribute('data-agent-id')) || 'agent_support_01';
  var themeColor = (currentScript && currentScript.getAttribute('data-theme')) || '#2563EB';
  var widgetTitle = (currentScript && currentScript.getAttribute('data-title')) || 'VoxAide Support';
  var apiUrl = (currentScript && currentScript.getAttribute('data-api-url')) || 'https://voxaide-ai.onrender.com';

  var isChatOpen = false;
  var isSpeaking = false;
  var conversationId = 'conv_' + Math.random().toString(36).substring(2, 10);

  // 2. Inject CSS Styles
  var style = document.createElement('style');
  style.innerHTML = `
    #voxaide-bubble-btn {
      position: fixed;
      bottom: 24px;
      right: 24px;
      width: 58px;
      height: 58px;
      border-radius: 50%;
      background: ${themeColor};
      box-shadow: 0 4px 20px rgba(37, 99, 235, 0.35);
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 999999;
      transition: transform 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
      border: none;
      outline: none;
    }
    #voxaide-bubble-btn:hover {
      transform: scale(1.08);
    }
    #voxaide-bubble-btn svg {
      width: 28px;
      height: 28px;
      fill: #FFFFFF;
    }
    #voxaide-window {
      position: fixed;
      bottom: 96px;
      right: 24px;
      width: 380px;
      max-width: calc(100vw - 32px);
      height: 540px;
      max-height: calc(100vh - 120px);
      background: #FFFFFF;
      border-radius: 16px;
      box-shadow: 0 12px 40px rgba(0, 0, 0, 0.16);
      display: none;
      flex-direction: column;
      overflow: hidden;
      z-index: 999999;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      border: 1px solid rgba(0,0,0,0.08);
    }
    #voxaide-header {
      background: ${themeColor};
      color: #FFFFFF;
      padding: 16px 20px;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }
    #voxaide-header .title-area {
      display: flex;
      align-items: center;
      gap: 10px;
    }
    #voxaide-header .avatar {
      width: 36px;
      height: 36px;
      border-radius: 50%;
      background: rgba(255,255,255,0.2);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 18px;
    }
    #voxaide-header .status {
      font-size: 11px;
      opacity: 0.85;
      display: flex;
      align-items: center;
      gap: 4px;
    }
    #voxaide-header .status-dot {
      width: 6px;
      height: 6px;
      background: #10B981;
      border-radius: 50%;
    }
    #voxaide-header .close-btn {
      background: transparent;
      border: none;
      color: #FFFFFF;
      font-size: 20px;
      cursor: pointer;
      opacity: 0.8;
    }
    #voxaide-messages {
      flex: 1;
      padding: 16px;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 12px;
      background: #F9FAFB;
    }
    .vox-msg {
      max-width: 82%;
      padding: 10px 14px;
      border-radius: 14px;
      font-size: 14px;
      line-height: 1.45;
      word-break: break-word;
    }
    .vox-bot {
      background: #FFFFFF;
      color: #1F2937;
      align-self: flex-start;
      border: 1px solid rgba(0,0,0,0.06);
      border-bottom-left-radius: 4px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .vox-user {
      background: ${themeColor};
      color: #FFFFFF;
      align-self: flex-end;
      border-bottom-right-radius: 4px;
    }
    #voxaide-footer {
      padding: 12px 14px;
      background: #FFFFFF;
      border-top: 1px solid rgba(0,0,0,0.08);
      display: flex;
      align-items: center;
      gap: 8px;
    }
    #voxaide-input {
      flex: 1;
      border: 1px solid rgba(0,0,0,0.15);
      border-radius: 20px;
      padding: 9px 14px;
      font-size: 14px;
      outline: none;
    }
    #voxaide-input:focus {
      border-color: ${themeColor};
    }
    .vox-action-btn {
      background: ${themeColor};
      border: none;
      border-radius: 50%;
      width: 36px;
      height: 36px;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      color: #FFFFFF;
    }
    .vox-mic-btn {
      background: #F3F4F6;
      color: #374151;
      border: 1px solid rgba(0,0,0,0.1);
      border-radius: 50%;
      width: 36px;
      height: 36px;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
    }
    .vox-mic-btn.active {
      background: #EF4444;
      color: #FFFFFF;
    }
    .vox-brand {
      text-align: center;
      font-size: 10px;
      color: #9CA3AF;
      padding-bottom: 6px;
      background: #FFFFFF;
    }
  `;
  document.head.appendChild(style);

  // 3. Create Widget DOM elements
  var bubbleBtn = document.createElement('button');
  bubbleBtn.id = 'voxaide-bubble-btn';
  bubbleBtn.innerHTML = `
    <svg viewBox="0 0 24 24"><path d="M12 2a9 9 0 0 0-9 9c0 2.4.95 4.6 2.5 6.2L4 21l4.1-1.3A8.96 8.96 0 0 0 12 20a9 9 0 0 0 9-9 9 9 0 0 0-9-9zm0 2a7 7 0 0 1 7 7 7 7 0 0 1-7 7c-.96 0-1.89-.2-2.73-.55l-.47-.2-2.43.78.8-2.34-.23-.46A6.97 6.97 0 0 1 5 11a7 7 0 0 1 7-7z"/></svg>
  `;

  var windowDiv = document.createElement('div');
  windowDiv.id = 'voxaide-window';
  windowDiv.innerHTML = `
    <div id="voxaide-header">
      <div class="title-area">
        <div class="avatar">🤖</div>
        <div>
          <div style="font-weight: 600; font-size: 14px;">${widgetTitle}</div>
          <div class="status"><span class="status-dot"></span> Online • AI Voice Ready</div>
        </div>
      </div>
      <button class="close-btn" id="voxaide-close">&times;</button>
    </div>
    <div id="voxaide-messages">
      <div class="vox-msg vox-bot">Hello! How can I help you today? You can type or tap the microphone to talk.</div>
    </div>
    <div id="voxaide-footer">
      <input type="text" id="voxaide-input" placeholder="Type a question..." />
      <button class="vox-mic-btn" id="voxaide-mic" title="Voice Input">🎙️</button>
      <button class="vox-action-btn" id="voxaide-send" title="Send">➤</button>
    </div>
    <div class="vox-brand">Powered by VoxAide Autonomous Voice AI</div>
  `;

  document.body.appendChild(bubbleBtn);
  document.body.appendChild(windowDiv);

  // 4. Attach Event Handlers
  var inputEl = document.getElementById('voxaide-input');
  var sendBtn = document.getElementById('voxaide-send');
  var micBtn = document.getElementById('voxaide-mic');
  var closeBtn = document.getElementById('voxaide-close');
  var messagesEl = document.getElementById('voxaide-messages');

  bubbleBtn.onclick = function () {
    isChatOpen = !isChatOpen;
    windowDiv.style.display = isChatOpen ? 'flex' : 'none';
    if (isChatOpen) inputEl.focus();
  };

  closeBtn.onclick = function () {
    isChatOpen = false;
    windowDiv.style.display = 'none';
  };

  function addMessage(text, role) {
    var div = document.createElement('div');
    div.className = 'vox-msg ' + (role === 'user' ? 'vox-user' : 'vox-bot');
    div.innerText = text;
    messagesEl.appendChild(div);
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  function speakText(text) {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      var utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 1.05;
      window.speechSynthesis.speak(utterance);
    }
  }

  function sendMessage(text) {
    if (!text || !text.trim()) return;
    addMessage(text, 'user');
    inputEl.value = '';

    // Send to VoxAide Agent API
    var endpoint = apiUrl + '/api/agent/companies/' + companyId + '/agent/chat';
    fetch(endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer dev_token_' + companyId,
        'X-Company-ID': companyId
      },
      body: JSON.stringify({
        message: text,
        agent_id: agentId,
        conversation_id: conversationId,
        channel: 'web_widget'
      })
    })
    .then(function (res) { return res.json(); })
    .then(function (data) {
      var botReply = data.response || 'I have recorded your request.';
      addMessage(botReply, 'bot');
      speakText(botReply);
    })
    .catch(function () {
      addMessage('Thank you for reaching out! Our team has received your message and will follow up shortly.', 'bot');
    });
  }

  sendBtn.onclick = function () {
    sendMessage(inputEl.value);
  };

  inputEl.onkeydown = function (e) {
    if (e.key === 'Enter') sendMessage(inputEl.value);
  };

  // 5. Speech Recognition for Voice Interaction
  micBtn.onclick = function () {
    var SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert('Speech recognition is not supported in this browser. Please type your message.');
      return;
    }

    if (isSpeaking) return;

    var recognition = new SpeechRecognition();
    recognition.lang = 'en-US';
    recognition.interimResults = false;

    recognition.onstart = function () {
      isSpeaking = true;
      micBtn.classList.add('active');
    };

    recognition.onresult = function (event) {
      var transcript = event.results[0][0].transcript;
      isSpeaking = false;
      micBtn.classList.remove('active');
      sendMessage(transcript);
    };

    recognition.onerror = function () {
      isSpeaking = false;
      micBtn.classList.remove('active');
    };

    recognition.onend = function () {
      isSpeaking = false;
      micBtn.classList.remove('active');
    };

    recognition.start();
  };
})();
