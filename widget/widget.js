(function () {
    const API_BASE = "http://localhost:8000"; // change this to your real server URL when deployed

    let sessionData = null;
    let mediaRecorder = null;
    let audioChunks = [];
    let isRecording = false;
    let typingEl = null;

    /* ------------------------------------------------------------------ */
    /*  External assets (fonts + Bootstrap Icons)                          */
    /* ------------------------------------------------------------------ */
    function injectExternalAssets() {
        if (!document.getElementById("ai-widget-fonts")) {
            const fontLink = document.createElement("link");
            fontLink.id = "ai-widget-fonts";
            fontLink.rel = "stylesheet";
            fontLink.href = "https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@500;600;700;800&family=Inter:wght@400;500;600&display=swap";
            document.head.appendChild(fontLink);
        }
        if (!document.getElementById("ai-widget-icons")) {
            const iconLink = document.createElement("link");
            iconLink.id = "ai-widget-icons";
            iconLink.rel = "stylesheet";
            iconLink.href = "https://cdnjs.cloudflare.com/ajax/libs/bootstrap-icons/1.11.3/font/bootstrap-icons.min.css";
            document.head.appendChild(iconLink);
        }
    }

    /* ------------------------------------------------------------------ */
    /*  Markup                                                              */
    /* ------------------------------------------------------------------ */
    function createWidgetHTML() {
        const container = document.createElement("div");
        container.id = "ai-widget-container";
        container.innerHTML = `
            <button id="ai-widget-bubble" aria-label="Open chat">
                <span id="ai-widget-bubble-ring"></span>
                <i class="bi bi-chat-dots-fill" id="ai-widget-bubble-icon"></i>
                <i class="bi bi-x-lg" id="ai-widget-bubble-icon-close"></i>
            </button>

            <div id="ai-widget-panel" role="dialog" aria-label="Chat assistant">
                <div id="ai-widget-header">
                    <div id="ai-widget-header-avatar">
                        <i class="bi bi-robot"></i>
                    </div>
                    <div id="ai-widget-header-text">
                        <span id="ai-widget-header-title">Assistant</span>
                        <span id="ai-widget-header-status"><i class="bi bi-circle-fill"></i>Online now</span>
                    </div>
                    <button id="ai-widget-close" aria-label="Close chat">
                        <i class="bi bi-x-lg"></i>
                    </button>
                </div>

                <div id="ai-widget-body">
                    <div id="ai-widget-login">
                        <div id="ai-widget-login-heading">
                            <h3>Let's get started</h3>
                            <p>Tell us a little about you before we dive in.</p>
                        </div>

                        <label class="ai-field">
                            <i class="bi bi-building"></i>
                            <input id="ai-widget-org" placeholder="Company name" autocomplete="organization" />
                        </label>
                        <label class="ai-field">
                            <i class="bi bi-person"></i>
                            <input id="ai-widget-name" placeholder="Your name" autocomplete="name" />
                        </label>
                        <label class="ai-field">
                            <i class="bi bi-envelope"></i>
                            <input id="ai-widget-email" placeholder="Your email" autocomplete="email" type="email" />
                        </label>

                        <button id="ai-widget-login-btn">
                            Start chat
                            <i class="bi bi-arrow-right"></i>
                        </button>
                    </div>

                    <div id="ai-widget-chat">
                        <div id="ai-widget-messages"></div>

                        <div id="ai-widget-input-row">
                            <button id="ai-widget-upload-btn" title="Attach a file" aria-label="Attach a file">
                                <i class="bi bi-paperclip"></i>
                            </button>
                            <input id="ai-widget-file" type="file" style="display:none;" />

                            <div id="ai-widget-input-wrap">
                                <input id="ai-widget-input" placeholder="Type a message…" autocomplete="off" />
                            </div>

                            <button id="ai-widget-mic-btn" title="Record a voice message" aria-label="Record a voice message">
                                <i class="bi bi-mic-fill"></i>
                            </button>
                            <button id="ai-widget-send" title="Send" aria-label="Send message">
                                <i class="bi bi-send-fill"></i>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(container);
    }

    /* ------------------------------------------------------------------ */
    /*  Styles                                                              */
    /* ------------------------------------------------------------------ */
    function injectStyles() {
        const style = document.createElement("style");
        style.textContent = `
            #ai-widget-container {
                --ink: #15162B;
                --ink-soft: #4A4B63;
                --muted: #9192AB;
                --paper: #FFFFFF;
                --paper-soft: #F6F6FB;
                --border: #EBEBF3;
                --accent-a: #6C5CE7;
                --accent-b: #00C2A8;
                --accent-solid: #5B4FE0;
                --accent-solid-dark: #4A3FD1;
                --danger: #FF5566;
                --radius-lg: 22px;
                --radius-md: 14px;
                --shadow-panel: 0 24px 60px -12px rgba(21, 22, 43, 0.28), 0 4px 16px rgba(21, 22, 43, 0.08);
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            }
            #ai-widget-container * { box-sizing: border-box; }

            /* ---------- Launcher bubble ---------- */
            #ai-widget-bubble {
                position: fixed; bottom: 22px; right: 22px;
                width: 60px; height: 60px; border-radius: 50%;
                background: linear-gradient(135deg, var(--accent-a), var(--accent-b));
                border: none; cursor: pointer;
                display: flex; align-items: center; justify-content: center;
                box-shadow: 0 10px 30px -6px rgba(108, 92, 231, 0.55);
                z-index: 999999;
                transition: transform 0.2s cubic-bezier(.34,1.56,.64,1), box-shadow 0.2s ease;
            }
            #ai-widget-bubble:hover {
                transform: scale(1.07);
                box-shadow: 0 14px 34px -6px rgba(108, 92, 231, 0.65);
            }
            #ai-widget-bubble:active { transform: scale(0.96); }
            #ai-widget-bubble-ring {
                position: absolute; inset: -6px; border-radius: 50%;
                background: conic-gradient(from 0deg, var(--accent-a), var(--accent-b), var(--accent-a));
                opacity: 0.35; z-index: -1;
                animation: ai-spin 6s linear infinite;
            }
            @media (prefers-reduced-motion: reduce) { #ai-widget-bubble-ring { animation: none; } }
            @keyframes ai-spin { to { transform: rotate(360deg); } }
            #ai-widget-bubble-icon, #ai-widget-bubble-icon-close {
                color: white; font-size: 24px;
                position: absolute; transition: opacity 0.15s ease, transform 0.2s ease;
            }
            #ai-widget-bubble-icon-close { opacity: 0; transform: scale(0.6) rotate(-45deg); font-size: 20px; }
            #ai-widget-container.ai-open #ai-widget-bubble-icon { opacity: 0; transform: scale(0.6) rotate(45deg); }
            #ai-widget-container.ai-open #ai-widget-bubble-icon-close { opacity: 1; transform: scale(1) rotate(0deg); }

            /* ---------- Panel ---------- */
            #ai-widget-panel {
                position: fixed; bottom: 96px; right: 22px;
                width: 380px; height: 600px; max-height: calc(100vh - 120px);
                background: var(--paper);
                border-radius: var(--radius-lg);
                box-shadow: var(--shadow-panel);
                display: flex; flex-direction: column; overflow: hidden;
                z-index: 999999;
                opacity: 0; transform: translateY(16px) scale(0.97);
                pointer-events: none;
                transform-origin: bottom right;
                transition: opacity 0.22s ease, transform 0.22s cubic-bezier(.2,.8,.2,1);
            }
            #ai-widget-container.ai-open #ai-widget-panel {
                opacity: 1; transform: translateY(0) scale(1); pointer-events: auto;
            }
            @media (max-width: 480px) {
                #ai-widget-panel {
                    right: 0; left: 0; bottom: 0; top: 0;
                    width: 100%; height: 100%; max-height: none;
                    border-radius: 0;
                }
                #ai-widget-bubble { bottom: 18px; right: 18px; }
            }

            /* ---------- Header ---------- */
            #ai-widget-header {
                flex-shrink: 0;
                background: linear-gradient(120deg, var(--ink) 0%, #262744 100%);
                padding: 18px 16px 18px 18px;
                display: flex; align-items: center; gap: 12px;
            }
            #ai-widget-header-avatar {
                width: 40px; height: 40px; border-radius: 12px; flex-shrink: 0;
                background: linear-gradient(135deg, var(--accent-a), var(--accent-b));
                display: flex; align-items: center; justify-content: center;
                color: white; font-size: 19px;
            }
            #ai-widget-header-text { display: flex; flex-direction: column; gap: 2px; flex: 1; min-width: 0; }
            #ai-widget-header-title {
                font-family: 'Plus Jakarta Sans', sans-serif; font-weight: 700;
                font-size: 15.5px; color: white; letter-spacing: -0.01em;
            }
            #ai-widget-header-status {
                font-size: 12px; color: rgba(255,255,255,0.68);
                display: flex; align-items: center; gap: 5px;
            }
            #ai-widget-header-status i { font-size: 7px; color: #3DDC97; }
            #ai-widget-close {
                width: 30px; height: 30px; border-radius: 9px; flex-shrink: 0;
                background: rgba(255,255,255,0.1); border: none; cursor: pointer;
                color: rgba(255,255,255,0.85); font-size: 13px;
                display: flex; align-items: center; justify-content: center;
                transition: background 0.15s ease;
            }
            #ai-widget-close:hover { background: rgba(255,255,255,0.2); }

            /* ---------- Body wrapper ---------- */
            #ai-widget-body { flex: 1; display: flex; flex-direction: column; min-height: 0; background: var(--paper); }

            /* ---------- Login ---------- */
            #ai-widget-login {
                padding: 26px 22px; display: flex; flex-direction: column; gap: 13px;
                overflow-y: auto;
            }
            #ai-widget-login-heading { margin-bottom: 6px; }
            #ai-widget-login-heading h3 {
                margin: 0 0 4px; font-family: 'Plus Jakarta Sans', sans-serif;
                font-weight: 700; font-size: 19px; color: var(--ink); letter-spacing: -0.01em;
            }
            #ai-widget-login-heading p { margin: 0; font-size: 13px; color: var(--muted); }
            .ai-field {
                display: flex; align-items: center; gap: 10px;
                border: 1.5px solid var(--border); border-radius: var(--radius-md);
                padding: 0 14px; background: var(--paper-soft);
                transition: border-color 0.15s ease, background 0.15s ease;
            }
            .ai-field i { color: var(--muted); font-size: 15px; flex-shrink: 0; }
            .ai-field:focus-within {
                border-color: var(--accent-a); background: var(--paper);
                box-shadow: 0 0 0 4px rgba(108, 92, 231, 0.1);
            }
            .ai-field input {
                border: none; outline: none; background: transparent;
                padding: 12px 0; font-size: 14px; color: var(--ink); width: 100%;
                font-family: 'Inter', sans-serif;
            }
            .ai-field input::placeholder { color: var(--muted); }
            #ai-widget-login-btn {
                margin-top: 6px; padding: 13px; border: none; border-radius: var(--radius-md);
                background: linear-gradient(135deg, var(--accent-a), var(--accent-solid));
                color: white; font-family: 'Plus Jakarta Sans', sans-serif; font-weight: 600;
                font-size: 14.5px; cursor: pointer;
                display: flex; align-items: center; justify-content: center; gap: 8px;
                box-shadow: 0 8px 20px -6px rgba(91, 79, 224, 0.55);
                transition: transform 0.15s ease, box-shadow 0.15s ease;
            }
            #ai-widget-login-btn:hover { transform: translateY(-1px); box-shadow: 0 10px 24px -6px rgba(91, 79, 224, 0.65); }
            #ai-widget-login-btn:active { transform: translateY(0); }
            #ai-widget-login-btn i { font-size: 14px; transition: transform 0.15s ease; }
            #ai-widget-login-btn:hover i { transform: translateX(3px); }

            /* ---------- Chat ---------- */
            #ai-widget-chat { flex: 1; display: none; flex-direction: column; min-height: 0; }
            #ai-widget-chat.ai-active { display: flex; }

            #ai-widget-messages {
                flex: 1; min-height: 0; overflow-y: auto; scroll-behavior: smooth;
                -webkit-overflow-scrolling: touch;
                padding: 18px 16px; display: flex; flex-direction: column; gap: 12px;
                background:
                    radial-gradient(circle at 100% 0%, rgba(108,92,231,0.05), transparent 45%),
                    var(--paper);
            }
            #ai-widget-messages::-webkit-scrollbar { width: 6px; }
            #ai-widget-messages::-webkit-scrollbar-track { background: transparent; }
            #ai-widget-messages::-webkit-scrollbar-thumb { background: #DADCE8; border-radius: 10px; }
            #ai-widget-messages::-webkit-scrollbar-thumb:hover { background: #C3C5D8; }
            #ai-widget-messages { scrollbar-width: thin; scrollbar-color: #DADCE8 transparent; }

            .ai-row { display: flex; align-items: flex-end; gap: 8px; max-width: 88%; animation: ai-rise 0.22s ease; }
            @keyframes ai-rise { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }
            .ai-row.user { align-self: flex-end; flex-direction: row-reverse; }
            .ai-row.bot { align-self: flex-start; }
            .ai-avatar {
                width: 26px; height: 26px; border-radius: 8px; flex-shrink: 0;
                display: flex; align-items: center; justify-content: center; font-size: 12px;
                margin-bottom: 2px;
            }
            .ai-row.bot .ai-avatar { background: linear-gradient(135deg, var(--accent-a), var(--accent-b)); color: white; }
            .ai-row.user .ai-avatar { background: var(--paper-soft); color: var(--ink-soft); border: 1px solid var(--border); }

            .ai-msg-col { display: flex; flex-direction: column; gap: 3px; min-width: 0; }
            .ai-row.user .ai-msg-col { align-items: flex-end; }
            .ai-msg {
                padding: 10px 14px; border-radius: 16px; font-size: 14px; line-height: 1.48;
                word-wrap: break-word; white-space: pre-wrap;
            }
            .ai-row.user .ai-msg {
                background: linear-gradient(135deg, var(--accent-a), var(--accent-solid));
                color: white; border-bottom-right-radius: 5px;
            }
            .ai-row.bot .ai-msg {
                background: var(--paper-soft); color: var(--ink); border: 1px solid var(--border);
                border-bottom-left-radius: 5px;
            }
            .ai-msg.ai-file-msg { display: flex; align-items: center; gap: 8px; }
            .ai-msg.ai-file-msg i { font-size: 16px; }

            .ai-rich-text p { margin: 0 0 8px; }
            .ai-rich-text p:last-child { margin-bottom: 0; }
            .ai-rich-text strong { font-weight: 700; color: var(--ink); }
            .ai-row.user .ai-rich-text strong { color: white; }
            .ai-rich-text em { font-style: italic; }
            .ai-rich-text code {
                background: rgba(21, 22, 43, 0.06); border: 1px solid rgba(21, 22, 43, 0.08);
                padding: 1.5px 6px; border-radius: 6px; font-size: 12.5px;
                font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
                color: #4A3FD1;
            }
            .ai-row.user .ai-rich-text code {
                background: rgba(255,255,255,0.18); border-color: rgba(255,255,255,0.25); color: white;
            }
            .ai-rich-text a { color: var(--accent-solid); font-weight: 600; text-decoration: underline; text-underline-offset: 2px; }
            .ai-row.user .ai-rich-text a { color: white; }
            .ai-rich-text ul { margin: 4px 0 8px; padding-left: 18px; }
            .ai-rich-text ul:last-child { margin-bottom: 0; }
            .ai-rich-text li { margin-bottom: 4px; }
            .ai-rich-text li:last-child { margin-bottom: 0; }
            .ai-rich-text br { line-height: 6px; }
            .ai-timestamp { font-size: 10.5px; color: var(--muted); padding: 0 3px; }

            /* typing indicator */
            .ai-typing-dots { display: flex; align-items: center; gap: 4px; padding: 4px 2px; }
            .ai-typing-dots span {
                width: 6px; height: 6px; border-radius: 50%; background: var(--muted);
                animation: ai-bounce 1.1s infinite ease-in-out;
            }
            .ai-typing-dots span:nth-child(2) { animation-delay: 0.15s; }
            .ai-typing-dots span:nth-child(3) { animation-delay: 0.3s; }
            @keyframes ai-bounce { 0%, 60%, 100% { transform: translateY(0); opacity: 0.5; } 30% { transform: translateY(-5px); opacity: 1; } }

            /* ---------- Input row ---------- */
            #ai-widget-input-row {
                flex-shrink: 0;
                display: flex; align-items: center; gap: 6px;
                padding: 12px 14px; border-top: 1px solid var(--border); background: var(--paper);
            }
            #ai-widget-input-wrap {
                flex: 1; min-width: 0; background: var(--paper-soft);
                border: 1.5px solid var(--border); border-radius: 22px;
                padding: 0 4px 0 15px; display: flex; align-items: center;
                transition: border-color 0.15s ease, background 0.15s ease;
            }
            #ai-widget-input-wrap:focus-within {
                border-color: var(--accent-a); background: var(--paper);
                box-shadow: 0 0 0 4px rgba(108, 92, 231, 0.1);
            }
            #ai-widget-input {
                flex: 1; min-width: 0; border: none; outline: none; background: transparent;
                padding: 11px 0; font-size: 14px; color: var(--ink); font-family: 'Inter', sans-serif;
            }
            #ai-widget-input::placeholder { color: var(--muted); }

            #ai-widget-send, #ai-widget-upload-btn, #ai-widget-mic-btn {
                width: 38px; height: 38px; flex-shrink: 0;
                border: none; border-radius: 50%; cursor: pointer;
                display: flex; align-items: center; justify-content: center; font-size: 14.5px;
                transition: background 0.15s ease, transform 0.15s ease, box-shadow 0.15s ease;
            }
            #ai-widget-upload-btn, #ai-widget-mic-btn {
                background: var(--paper-soft); color: var(--ink-soft); border: 1px solid var(--border);
            }
            #ai-widget-upload-btn:hover, #ai-widget-mic-btn:hover { background: #EDEDF7; color: var(--accent-solid); }
            #ai-widget-send {
                background: linear-gradient(135deg, var(--accent-a), var(--accent-solid));
                color: white; box-shadow: 0 6px 16px -4px rgba(91, 79, 224, 0.55);
            }
            #ai-widget-send:hover { transform: translateY(-1px) scale(1.03); }
            #ai-widget-send:active { transform: translateY(0) scale(0.97); }

            #ai-widget-mic-btn.recording {
                background: var(--danger); color: white; border-color: var(--danger);
                animation: ai-pulse 1.2s infinite;
            }
            @keyframes ai-pulse {
                0% { box-shadow: 0 0 0 0 rgba(255, 85, 102, 0.5); }
                70% { box-shadow: 0 0 0 9px rgba(255, 85, 102, 0); }
                100% { box-shadow: 0 0 0 0 rgba(255, 85, 102, 0); }
            }
        `;
        document.head.appendChild(style);
    }

    /* ------------------------------------------------------------------ */
    /*  Message rendering                                                   */
    /* ------------------------------------------------------------------ */
    function formatTime() {
        return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    }

    function scrollToBottom() {
        const messages = document.getElementById("ai-widget-messages");
        messages.scrollTop = messages.scrollHeight;
    }

    /* ---------- Minimal, safe markdown renderer for bot replies ---------- */
    function escapeHTML(str) {
        return str
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#39;");
    }

    function renderInline(text) {
        let out = escapeHTML(text);
        // inline code `code`
        out = out.replace(/`([^`]+)`/g, "<code>$1</code>");
        // bold: **text** or __text__
        out = out.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
        out = out.replace(/__([^_]+)__/g, "<strong>$1</strong>");
        // italics: *text* or _text_ (after bold so ** isn't caught here)
        out = out.replace(/\*([^*]+)\*/g, "<em>$1</em>");
        out = out.replace(/(?<![A-Za-z0-9])_([^_]+)_(?![A-Za-z0-9])/g, "<em>$1</em>");
        // links: [label](url)
        out = out.replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');
        return out;
    }

    function renderMarkdown(text) {
        const lines = text.split("\n");
        let html = "";
        let inList = false;

        for (const rawLine of lines) {
            const line = rawLine.trim();
            const isBullet = /^[-*]\s+/.test(line);

            if (isBullet) {
                if (!inList) { html += "<ul>"; inList = true; }
                html += `<li>${renderInline(line.replace(/^[-*]\s+/, ""))}</li>`;
                continue;
            }
            if (inList) { html += "</ul>"; inList = false; }

            if (line === "") { html += "<br>"; continue; }
            html += `<p>${renderInline(line)}</p>`;
        }
        if (inList) html += "</ul>";
        return html;
    }

    function addMessage(text, sender, options = {}) {
        const messages = document.getElementById("ai-widget-messages");
        const row = document.createElement("div");
        row.className = `ai-row ${sender}`;

        const avatar = document.createElement("div");
        avatar.className = "ai-avatar";
        avatar.innerHTML = sender === "bot" ? '<i class="bi bi-robot"></i>' : '<i class="bi bi-person-fill"></i>';

        const col = document.createElement("div");
        col.className = "ai-msg-col";

        const bubble = document.createElement("div");
        bubble.className = "ai-msg" + (options.fileIcon ? " ai-file-msg" : "");
        if (options.fileIcon) {
            bubble.innerHTML = `<i class="bi ${options.fileIcon}"></i><span></span>`;
            bubble.querySelector("span").textContent = text;
        } else if (sender === "bot") {
            bubble.classList.add("ai-rich-text");
            bubble.innerHTML = renderMarkdown(text);
        } else {
            bubble.textContent = text;
        }

        const time = document.createElement("span");
        time.className = "ai-timestamp";
        time.textContent = formatTime();

        col.appendChild(bubble);
        col.appendChild(time);
        row.appendChild(avatar);
        row.appendChild(col);
        messages.appendChild(row);
        scrollToBottom();
        return row;
    }

    function showTyping() {
        if (typingEl) return;
        const messages = document.getElementById("ai-widget-messages");
        const row = document.createElement("div");
        row.className = "ai-row bot";
        row.innerHTML = `
            <div class="ai-avatar"><i class="bi bi-robot"></i></div>
            <div class="ai-msg-col">
                <div class="ai-msg ai-typing-dots"><span></span><span></span><span></span></div>
            </div>
        `;
        messages.appendChild(row);
        typingEl = row;
        scrollToBottom();
    }

    function hideTyping() {
        if (typingEl) {
            typingEl.remove();
            typingEl = null;
        }
    }

    /* ------------------------------------------------------------------ */
    /*  Handlers                                                            */
    /* ------------------------------------------------------------------ */
    async function handleLogin() {
        const org = document.getElementById("ai-widget-org").value.trim();
        const name = document.getElementById("ai-widget-name").value.trim();
        const email = document.getElementById("ai-widget-email").value.trim();

        if (!org || !name || !email) {
            alert("Please fill in all fields.");
            return;
        }

        const btn = document.getElementById("ai-widget-login-btn");
        const originalHTML = btn.innerHTML;
        btn.innerHTML = `<i class="bi bi-arrow-repeat"></i> Connecting…`;
        btn.disabled = true;

        try {
            const response = await fetch(`${API_BASE}/user/lookup`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ organization_name: org, name: name, email: email })
            });

            if (!response.ok) {
                const err = await response.json();
                alert(err.error || "Login failed");
                return;
            }

            sessionData = await response.json();

            document.getElementById("ai-widget-login").style.display = "none";
            document.getElementById("ai-widget-chat").classList.add("ai-active");
            addMessage(`Welcome, **${name}**! How can I help you today?`, "bot");
        } finally {
            btn.innerHTML = originalHTML;
            btn.disabled = false;
        }
    }

    async function handleSend() {
        const input = document.getElementById("ai-widget-input");
        const message = input.value.trim();
        if (!message || !sessionData) return;

        addMessage(message, "user");
        input.value = "";
        showTyping();

        try {
            const response = await fetch(`${API_BASE}/chat`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    organization_id: sessionData.organization_id,
                    session_id: sessionData.session_id,
                    conversation_id: sessionData.conversation_id,
                    message: message
                })
            });

            const data = await response.json();
            hideTyping();
            addMessage(data.reply || "Sorry, something went wrong.", "bot");
        } catch (err) {
            hideTyping();
            addMessage("Sorry, something went wrong.", "bot");
        }
    }

    async function handleUpload(file) {
        if (!file || !sessionData) return;

        const formData = new FormData();
        formData.append("organization_id", sessionData.organization_id);
        formData.append("user_id", sessionData.user_id);
        formData.append("file", file);

        addMessage(file.name, "user", { fileIcon: "bi-file-earmark-arrow-up-fill" });
        showTyping();

        try {
            const response = await fetch(`${API_BASE}/upload`, {
                method: "POST",
                body: formData
            });

            const data = await response.json();
            hideTyping();
            if (response.ok) {
                addMessage(`Document processed: ${data.filename} (${data.chunks_created} chunks, strategy: ${data.strategy})`, "bot", { fileIcon: "bi-check-circle-fill" });
            } else {
                addMessage(`Upload failed: ${data.error}`, "bot");
            }
        } catch (err) {
            hideTyping();
            addMessage("Upload failed. Please try again.", "bot");
        }
    }

    async function startRecording() {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        audioChunks = [];

        mediaRecorder.ondataavailable = (e) => audioChunks.push(e.data);
        mediaRecorder.onstop = handleRecordingStop;

        mediaRecorder.start();
        const micBtn = document.getElementById("ai-widget-mic-btn");
        micBtn.classList.add("recording");
        micBtn.innerHTML = '<i class="bi bi-stop-fill"></i>';
    }

    function stopRecording() {
        if (mediaRecorder && mediaRecorder.state !== "inactive") {
            mediaRecorder.stop();
        }
        const micBtn = document.getElementById("ai-widget-mic-btn");
        micBtn.classList.remove("recording");
        micBtn.innerHTML = '<i class="bi bi-mic-fill"></i>';
    }

    async function handleRecordingStop() {
        const audioBlob = new Blob(audioChunks, { type: "audio/webm" });

        addMessage("Voice message", "user", { fileIcon: "bi-mic-fill" });
        showTyping();

        try {
            const formData = new FormData();
            formData.append("audio", audioBlob, "recording.webm");

            const transcribeRes = await fetch(`${API_BASE}/voice/transcribe`, {
                method: "POST",
                body: formData
            });
            const transcribeData = await transcribeRes.json();
            const userText = transcribeData.text;

            const chatRes = await fetch(`${API_BASE}/chat`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    organization_id: sessionData.organization_id,
                    session_id: sessionData.session_id,
                    conversation_id: sessionData.conversation_id,
                    message: userText
                })
            });
            const chatData = await chatRes.json();
            hideTyping();
            addMessage(chatData.reply, "bot");

            const speakRes = await fetch(`${API_BASE}/voice/speak`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ text: chatData.reply })
            });
            const audioReplyBlob = await speakRes.blob();
            const audioUrl = URL.createObjectURL(audioReplyBlob);
            new Audio(audioUrl).play();
        } catch (err) {
            hideTyping();
            addMessage("Sorry, I couldn't process that voice message.", "bot");
        }
    }

    /* ------------------------------------------------------------------ */
    /*  Init                                                                */
    /* ------------------------------------------------------------------ */
    function init() {
        injectExternalAssets();
        injectStyles();
        createWidgetHTML();

        const container = document.getElementById("ai-widget-container");
        const panel = document.getElementById("ai-widget-panel");

        document.getElementById("ai-widget-bubble").onclick = () => {
            container.classList.toggle("ai-open");
        };
        document.getElementById("ai-widget-close").onclick = () => {
            container.classList.remove("ai-open");
        };
        document.getElementById("ai-widget-login-btn").onclick = handleLogin;
        document.getElementById("ai-widget-send").onclick = handleSend;
        document.getElementById("ai-widget-input").addEventListener("keypress", (e) => {
            if (e.key === "Enter") handleSend();
        });
        document.getElementById("ai-widget-org").addEventListener("keypress", (e) => {
            if (e.key === "Enter") handleLogin();
        });
        document.getElementById("ai-widget-name").addEventListener("keypress", (e) => {
            if (e.key === "Enter") handleLogin();
        });
        document.getElementById("ai-widget-email").addEventListener("keypress", (e) => {
            if (e.key === "Enter") handleLogin();
        });
        document.getElementById("ai-widget-upload-btn").onclick = () => {
            document.getElementById("ai-widget-file").click();
        };
        document.getElementById("ai-widget-file").addEventListener("change", (e) => {
            handleUpload(e.target.files[0]);
        });
        document.getElementById("ai-widget-mic-btn").onclick = () => {
            if (!sessionData) {
                alert("Please log in first.");
                return;
            }
            if (!isRecording) {
                startRecording();
                isRecording = true;
            } else {
                stopRecording();
                isRecording = false;
            }
        };

        // Close panel on outside click (desktop only, doesn't fight mobile full-screen)
        document.addEventListener("click", (e) => {
            if (window.innerWidth <= 480) return;
            if (!container.contains(e.target)) {
                container.classList.remove("ai-open");
            }
        });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();