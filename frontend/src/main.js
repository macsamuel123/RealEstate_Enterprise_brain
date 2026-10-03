/**
 * AI Chief of Staff Dashboard — JARVIS Integration
 * Entry point for the web-based command center
 */

import { loadConfig } from './services/config.js';

// Mock context object (JARVIS uses this pattern)
const ctx = {
    env: {
        platform: 'web',
        os: navigator.platform,
        isElectron: typeof window !== 'undefined' && window.electron !== undefined,
    },
    paths: {
        config: '/src/config/config.json',
    },
    state: {
        loading: true,
        config: null,
        widgets: {},
    },
    cache: new Map(),
    async loadConfig() {
        console.log('Loading configuration...');
        const response = await fetch(this.paths.config);
        if (!response.ok) throw new Error('Failed to load config');
        this.state.config = await response.json();
        console.log('Configuration loaded:', this.state.config);
        return this.state.config;
    },
};

/**
 * Initialize the dashboard
 */
async function main() {
    try {
        console.log('🚀 Starting Chief of Staff Dashboard...');

        // Load configuration
        await ctx.loadConfig();

        // Initialize dashboard
        const app = document.getElementById('app');
        app.innerHTML = '';

        // Create dashboard container
        const dashboard = document.createElement('div');
        dashboard.id = 'jarvis-dashboard';
        dashboard.style.cssText = `
            width: 100%;
            height: 100vh;
            background: linear-gradient(135deg, ${ctx.state.config.theme.bg} 0%, #000000 100%);
            color: ${ctx.state.config.theme.text};
            overflow: hidden;
            display: flex;
            flex-direction: column;
        `;

        app.appendChild(dashboard);

        // Load and render widgets based on layout
        await renderLayout(ctx, dashboard);

        ctx.state.loading = false;
        console.log('✅ Dashboard initialized successfully');

    } catch (error) {
        console.error('❌ Dashboard initialization failed:', error);
        document.getElementById('app').innerHTML = `
            <div style="
                height: 100vh;
                background: #0B0E14;
                color: #FF2E63;
                display: flex;
                align-items: center;
                justify-content: center;
                flex-direction: column;
                font-family: monospace;
                padding: 20px;
            ">
                <h1>System Error</h1>
                <p>${error.message}</p>
                <details style="margin-top: 20px; color: #E0E0E0;">
                    <summary>Stack Trace</summary>
                    <pre style="margin-top: 10px; overflow-x: auto;">${error.stack}</pre>
                </details>
            </div>
        `;
    }
}

/**
 * Render layout based on config
 */
async function renderLayout(ctx, container) {
    const layout = ctx.state.config.layout || [];

    for (const widget of layout) {
        const widgetEl = createWidgetElement(widget, ctx);
        container.appendChild(widgetEl);
    }
}

/**
 * Create widget element
 */
function createWidgetElement(widgetConfig, ctx) {
    const type = widgetConfig.type || 'unknown';
    const element = document.createElement('div');
    element.className = `widget widget-${type}`;
    element.dataset.widgetType = type;

    // Apply styling
    element.style.cssText = `
        padding: 16px;
        margin: 8px;
        background: rgba(18, 24, 36, 0.7);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(0, 240, 255, 0.2);
        border-radius: 8px;
        font-size: 13px;
        line-height: 1.5;
    `;

    // Render specific widget content
    renderWidgetContent(element, widgetConfig, ctx);

    return element;
}

/**
 * Render widget-specific content
 */
function renderWidgetContent(element, config, ctx) {
    const type = config.type;

    switch (type) {
        case 'header':
            renderHeader(element, ctx);
            break;
        case 'jarvis-voice-command':
            renderVoiceCommand(element, ctx);
            break;
        case 'operational-heartbeat':
            renderOperationalHeartbeat(element, ctx);
            break;
        case 'agent-squad':
            renderAgentSquad(element, ctx);
            break;
        case 'approval-queue':
            renderApprovalQueue(element, ctx);
            break;
        case 'recent-activity':
            renderRecentActivity(element, ctx);
            break;
        case 'row':
            renderRow(element, config, ctx);
            break;
        case 'footer':
            renderFooter(element, ctx);
            break;
        default:
            element.innerHTML = `<p style="color: #FFB800;">⚠️ Widget type not implemented: ${type}</p>`;
    }
}

/**
 * Render header
 */
function renderHeader(element, ctx) {
    const config = ctx.state.config.dashboard;
    element.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
            <div>
                <h1 style="font-size: 24px; color: #00F0FF; margin: 0; text-shadow: 0 0 10px currentColor;">
                    ${config.title}
                </h1>
                <p style="font-size: 12px; color: #6b7b8d; margin: 4px 0 0 0;">
                    ${config.subtitle}
                </p>
            </div>
            <div style="text-align: right; font-size: 12px; color: #00FF87;">
                <div>🟢 ${config.statusText}</div>
                <div id="clock" style="margin-top: 4px;"></div>
            </div>
        </div>
    `;

    // Update clock
    const clockEl = element.querySelector('#clock');
    if (clockEl) {
        setInterval(() => {
            clockEl.textContent = new Date().toLocaleTimeString();
        }, 1000);
    }
}

/**
 * Render voice command widget
 */
function renderVoiceCommand(element, ctx) {
    element.style.flex = '1';
    element.innerHTML = `
        <style>
            @keyframes pulse-glow {
                0%, 100% { transform: scale(1); opacity: 0.5; }
                50% { transform: scale(1.1); opacity: 0.8; }
            }
            @keyframes rotate {
                from { transform: rotate(0deg); }
                to { transform: rotate(360deg); }
            }
            @keyframes core-pulse {
                0%, 100% {
                    transform: scale(1);
                    box-shadow: 0 0 30px rgba(0, 240, 255, 0.6), 0 0 60px rgba(138, 43, 226, 0.3);
                }
                50% {
                    transform: scale(1.1);
                    box-shadow: 0 0 50px rgba(0, 240, 255, 0.8), 0 0 100px rgba(138, 43, 226, 0.5);
                }
            }
            @keyframes wave {
                0%, 100% { height: 20%; }
                50% { height: 100%; }
            }
            .orbit { position: absolute; border-radius: 50%; border: 2px solid; }
            .orbit-1 { width: 200px; height: 200px; border-color: rgba(0, 240, 255, 0.3); animation: rotate 8s linear infinite; }
            .orbit-2 { width: 140px; height: 140px; border-color: rgba(138, 43, 226, 0.4); animation: rotate 6s linear reverse infinite; }
            .orbit-3 { width: 80px; height: 80px; border-color: rgba(0, 240, 255, 0.5); animation: rotate 4s linear infinite; }
            .core { position: absolute; width: 50px; height: 50px; background: radial-gradient(circle at 35% 35%, rgba(0, 240, 255, 0.8), rgba(138, 43, 226, 0.4)); border-radius: 50%; animation: core-pulse 2s ease-in-out infinite; }
            .waveform { display: flex; align-items: center; justify-content: center; gap: 3px; height: 50px; }
            .wave-bar { width: 3px; background: linear-gradient(to top, #00F0FF, #8A2BE2); border-radius: 2px; animation: wave 0.8s ease-in-out infinite; }
        </style>
        <div style="display: flex; flex-direction: column; height: 100%; justify-content: space-between;">
            <!-- JARVIS CORE & WAVEFORMS -->
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; align-items: center; padding: 20px; background: rgba(0, 0, 0, 0.2); border-radius: 8px; margin-bottom: 12px;">
                <!-- Animated Core -->
                <div style="position: relative; width: 220px; height: 220px; margin: 0 auto;">
                    <div class="orbit orbit-1"></div>
                    <div class="orbit orbit-2"></div>
                    <div class="orbit orbit-3"></div>
                    <div class="core" style="top: 50%; left: 50%; transform: translate(-50%, -50%);"></div>
                </div>

                <!-- Waveforms -->
                <div style="display: flex; flex-direction: column; gap: 15px;">
                    <div>
                        <div style="font-size: 11px; color: #6b7b8d; margin-bottom: 6px;">🎙️ Input</div>
                        <div class="waveform">
                            <div class="wave-bar" style="animation-delay: 0s;"></div>
                            <div class="wave-bar" style="animation-delay: 0.1s;"></div>
                            <div class="wave-bar" style="animation-delay: 0.2s;"></div>
                            <div class="wave-bar" style="animation-delay: 0.3s;"></div>
                            <div class="wave-bar" style="animation-delay: 0.4s;"></div>
                            <div class="wave-bar" style="animation-delay: 0.5s;"></div>
                        </div>
                    </div>
                    <div>
                        <div style="font-size: 11px; color: #6b7b8d; margin-bottom: 6px;">⚡ Output</div>
                        <div class="waveform">
                            <div class="wave-bar" style="animation-delay: 0.2s;"></div>
                            <div class="wave-bar" style="animation-delay: 0.3s;"></div>
                            <div class="wave-bar" style="animation-delay: 0.4s;"></div>
                            <div class="wave-bar" style="animation-delay: 0.5s;"></div>
                            <div class="wave-bar" style="animation-delay: 0.6s;"></div>
                            <div class="wave-bar" style="animation-delay: 0.7s;"></div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- TRANSCRIPT -->
            <div id="voice-transcript" style="
                background: rgba(0, 0, 0, 0.3);
                border-left: 3px solid #8A2BE2;
                padding: 12px;
                border-radius: 4px;
                max-height: 80px;
                overflow-y: auto;
                min-height: 40px;
                font-size: 12px;
                line-height: 1.5;
            ">
                <p style="color: #6b7b8d; font-size: 11px; margin: 0;">
                    🎤 System ready. Listening...
                </p>
            </div>

            <!-- INPUT & CONTROLS -->
            <div style="display: flex; gap: 8px; margin-top: 12px;">
                <input
                    type="text"
                    id="voice-input"
                    placeholder="Type a command or press 🎤 to speak..."
                    style="
                        flex: 1;
                        background: rgba(18, 24, 36, 0.8);
                        border: 1px solid rgba(0, 240, 255, 0.3);
                        color: #E0E0E0;
                        padding: 8px 12px;
                        border-radius: 4px;
                        font-family: inherit;
                        font-size: 12px;
                    "
                />
                <button id="send-btn" style="
                    padding: 8px 16px;
                    background: linear-gradient(135deg, #00F0FF, #8A2BE2);
                    border: none;
                    color: white;
                    border-radius: 4px;
                    cursor: pointer;
                    font-weight: 600;
                    font-size: 12px;
                ">
                    Send
                </button>
            </div>
        </div>
    `;

    // Add send button interactivity
    setTimeout(() => {
        const sendBtn = element.querySelector('#send-btn');
        if (sendBtn) {
            sendBtn.addEventListener('click', () => {
                const input = element.querySelector('#voice-input');
                if (input && input.value.trim()) {
                    const transcript = element.querySelector('#voice-transcript');
                    const msg = document.createElement('div');
                    msg.style.cssText = 'color: #E0E0E0; margin-top: 6px;';
                    msg.textContent = `You: ${input.value}`;
                    transcript.appendChild(msg);
                    transcript.scrollTop = transcript.scrollHeight;
                    input.value = '';
                }
            });
        }
    }, 100);
}

/**
 * Render operational heartbeat widget
 */
function renderOperationalHeartbeat(element, ctx) {
    element.innerHTML = `
        <h3 style="color: #00F0FF; margin-bottom: 12px; display: flex; align-items: center; gap: 6px;">
            ⚕️ Operational Heartbeat
        </h3>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
            <div style="background: rgba(0, 0, 0, 0.2); padding: 12px; border-radius: 4px;">
                <div style="font-size: 11px; color: #6b7b8d;">System Integrity</div>
                <div style="font-size: 20px; color: #00FF87; font-weight: bold; margin-top: 6px;">87%</div>
            </div>
            <div style="background: rgba(0, 0, 0, 0.2); padding: 12px; border-radius: 4px;">
                <div style="font-size: 11px; color: #6b7b8d;">Response Time</div>
                <div style="font-size: 20px; color: #00F0FF; font-weight: bold; margin-top: 6px;">4.2 min</div>
            </div>
            <div style="background: rgba(0, 0, 0, 0.2); padding: 12px; border-radius: 4px;">
                <div style="font-size: 11px; color: #6b7b8d;">Pipeline Value</div>
                <div style="font-size: 20px; color: #8A2BE2; font-weight: bold; margin-top: 6px;">$2.4M</div>
            </div>
            <div style="background: rgba(255, 46, 99, 0.1); padding: 12px; border-radius: 4px; border-left: 2px solid #FF2E63;">
                <div style="font-size: 11px; color: #6b7b8d;">Anomalies</div>
                <div style="font-size: 20px; color: #FF2E63; font-weight: bold; margin-top: 6px;">3 Active</div>
            </div>
        </div>
    `;
}

/**
 * Render agent squad
 */
function renderAgentSquad(element, ctx) {
    const agents = ctx.state.config.widgets.agentSquad.agents || [];
    element.innerHTML = `
        <h3 style="color: #8A2BE2; margin-bottom: 12px; display: flex; align-items: center; gap: 6px;">
            🤖 Agent Squad
        </h3>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 8px;">
            ${agents.map(agent => `
                <div style="
                    background: rgba(0, 0, 0, 0.2);
                    padding: 8px;
                    border-radius: 4px;
                    border-left: 2px solid ${agent.color};
                    cursor: pointer;
                    transition: all 0.2s;
                ">
                    <div style="font-size: 11px; color: #6b7b8d;">${agent.role}</div>
                    <div style="font-size: 12px; color: ${agent.color}; font-weight: 600; margin-top: 4px;">
                        ${agent.name.split(' ')[0]}
                    </div>
                    <div style="font-size: 10px; color: #00FF87; margin-top: 4px;">🟢 Active</div>
                </div>
            `).join('')}
        </div>
    `;
}

/**
 * Render approval queue
 */
function renderApprovalQueue(element, ctx) {
    element.innerHTML = `
        <h3 style="color: #FFB800; margin-bottom: 12px; display: flex; align-items: center; gap: 6px;">
            ⚠️ Approval Queue
        </h3>
        <div style="display: flex; flex-direction: column; gap: 8px;">
            <div style="background: rgba(0, 255, 135, 0.1); border-left: 2px solid #00FF87; padding: 10px; border-radius: 4px;">
                <div style="font-size: 11px; color: #00FF87; font-weight: 600;">Send Email</div>
                <div style="font-size: 12px; color: #E0E0E0; margin-top: 4px;">Lead Qualifier → Follow-up on Bridgeland</div>
                <div style="display: flex; gap: 4px; margin-top: 6px;">
                    <button style="flex: 1; padding: 4px; background: rgba(0, 255, 135, 0.2); border: 1px solid #00FF87; color: #00FF87; cursor: pointer; border-radius: 2px; font-size: 10px;">✓ Approve</button>
                    <button style="flex: 1; padding: 4px; background: rgba(255, 46, 99, 0.2); border: 1px solid #FF2E63; color: #FF2E63; cursor: pointer; border-radius: 2px; font-size: 10px;">✕ Deny</button>
                </div>
            </div>
            <div style="background: rgba(255, 184, 0, 0.1); border-left: 2px solid #FFB800; padding: 10px; border-radius: 4px;">
                <div style="font-size: 11px; color: #FFB800; font-weight: 600;">Update CRM Deal</div>
                <div style="font-size: 12px; color: #E0E0E0; margin-top: 4px;">Op. Heartbeat → Move to Proposal (87% prob)</div>
                <div style="display: flex; gap: 4px; margin-top: 6px;">
                    <button style="flex: 1; padding: 4px; background: rgba(0, 255, 135, 0.2); border: 1px solid #00FF87; color: #00FF87; cursor: pointer; border-radius: 2px; font-size: 10px;">✓ Approve</button>
                    <button style="flex: 1; padding: 4px; background: rgba(255, 46, 99, 0.2); border: 1px solid #FF2E63; color: #FF2E63; cursor: pointer; border-radius: 2px; font-size: 10px;">✕ Deny</button>
                </div>
            </div>
        </div>
    `;
}

/**
 * Render recent activity
 */
function renderRecentActivity(element, ctx) {
    element.innerHTML = `
        <h3 style="color: #00D4FF; margin-bottom: 12px;">📋 Recent Activity</h3>
        <div style="font-size: 12px; line-height: 1.8; color: #E0E0E0;">
            <div>✓ Lead qualified: Michael Johnson - pre-approved buyer</div>
            <div style="margin-top: 6px;">✓ Email sent: Follow-up on Bridgeland property</div>
            <div style="margin-top: 6px;">⚠️ Anomaly: Agent prospect cold for 48h</div>
            <div style="margin-top: 6px;">✓ Meeting booked: Recruiting call with Sarah Chen</div>
        </div>
    `;
}

/**
 * Render row widget
 */
function renderRow(element, config, ctx) {
    element.style.cssText = `
        display: grid;
        grid-template-columns: repeat(${config.columns}, 1fr);
        gap: 8px;
        margin: 8px;
        padding: 0;
        background: transparent;
        border: none;
    `;

    config.widgets.forEach(widgetType => {
        const childWidget = createWidgetElement({ type: widgetType }, ctx);
        element.appendChild(childWidget);
    });
}

/**
 * Render footer
 */
function renderFooter(element, ctx) {
    element.innerHTML = `
        <div style="
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 12px;
            color: #6b7b8d;
            margin-top: auto;
            padding-top: 16px;
            border-top: 1px solid rgba(0, 240, 255, 0.1);
        ">
            <div>AI Chief of Staff v0.1.0</div>
            <div>Backend: http://localhost:8000</div>
            <div>Ready to serve</div>
        </div>
    `;
}

// Start the dashboard
main();
