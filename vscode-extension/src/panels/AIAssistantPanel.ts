/**
 * AI助手Webview面板
 */
import * as vscode from 'vscode';
import { APIClient } from '../services/APIClient';
import { CppCodeAnalyzer } from '../analyzer/CppCodeAnalyzer';
import { Configuration } from '../services/Configuration';

export class AIAssistantPanel {
    public static readonly viewType = 'cppAIAssistant.panel';
    private static panels: Map<string, AIAssistantPanel> = new Map();

    private readonly panel: vscode.WebviewPanel;
    private readonly extensionUri: vscode.Uri;
    private readonly apiClient: APIClient;
    private readonly codeAnalyzer: CppCodeAnalyzer;
    private readonly config: Configuration;
    private disposables: vscode.Disposable[] = [];

    private constructor(
        panel: vscode.WebviewPanel,
        extensionUri: vscode.Uri,
        apiClient: APIClient,
        codeAnalyzer: CppCodeAnalyzer,
        config: Configuration
    ) {
        this.panel = panel;
        this.extensionUri = extensionUri;
        this.apiClient = apiClient;
        this.codeAnalyzer = codeAnalyzer;
        this.config = config;

        // 设置Webview消息处理
        this.panel.webview.onDidReceiveMessage(
            this.handleMessage.bind(this),
            null,
            this.disposables
        );

        // 处理面板关闭
        this.panel.onDidDispose(
            () => this.dispose(),
            null,
            this.disposables
        );

        // 设置初始内容
        this.setInitialContent();
    }

    public static createOrShow(
        extensionUri: vscode.Uri,
        apiClient: APIClient,
        codeAnalyzer?: CppCodeAnalyzer,
        config?: Configuration
    ): AIAssistantPanel {
        const column = vscode.window.activeTextEditor?.viewColumn || vscode.ViewColumn.One;

        // 查找已存在的面板
        const existing = this.panels.get('main');
        if (existing) {
            existing.panel.reveal(column);
            return existing;
        }

        // 创建新面板
        const panel = vscode.window.createWebviewPanel(
            this.viewType,
            'C++ AI Assistant',
            column,
            {
                enableScripts: true,
                retainContextWhenHidden: true,
                localResourceRoots: [
                    vscode.Uri.joinPath(extensionUri, 'media')
                ]
            }
        );

        // 注意：config需要在外部传入
        const instance = new AIAssistantPanel(
            panel,
            extensionUri,
            apiClient,
            codeAnalyzer || new CppCodeAnalyzer(),
            config!
        );

        this.panels.set('main', instance);
        return instance;
    }

    private async handleMessage(message: any): Promise<void> {
        switch (message.type) {
            case 'explain':
                await this.handleExplain(message.code, message.language);
                break;
            case 'refactor':
                await this.handleRefactor(message.code, message.type);
                break;
            case 'review':
                await this.handleReview(message.code);
                break;
            case 'test':
                await this.handleTestGeneration(message.code, message.framework);
                break;
            case 'analyze':
                await this.handleLocalAnalysis(message.code);
                break;
            case 'sync':
                await this.handleSync();
                break;
            case 'showCode':
                this.showCode(message.code, message.language);
                break;
        }
    }

    private async handleExplain(code: string, language: string): Promise<void> {
        this.updatePanelState('loading', '正在分析代码...');

        try {
            const result = await this.apiClient.explainCode(code, language);
            this.updatePanelState('result', {
                title: '代码解释',
                content: result
            });
        } catch (error) {
            this.updatePanelState('error', `解释失败: ${error}`);
        }
    }

    private async handleRefactor(code: string, refactorType: string): Promise<void> {
        this.updatePanelState('loading', '正在生成重构建议...');

        try {
            const result = await this.apiClient.refactorCode(code, refactorType);
            this.updatePanelState('result', {
                title: '重构建议',
                content: JSON.stringify(result, null, 2)
            });
        } catch (error) {
            this.updatePanelState('error', `重构分析失败: ${error}`);
        }
    }

    private async handleReview(code: string): Promise<void> {
        this.updatePanelState('loading', '正在进行代码审查...');

        try {
            const result = await this.apiClient.reviewCode(code);
            this.updatePanelState('review', result);
        } catch (error) {
            this.updatePanelState('error', `代码审查失败: ${error}`);
        }
    }

    private async handleTestGeneration(code: string, framework: string): Promise<void> {
        this.updatePanelState('loading', '正在生成测试用例...');

        try {
            const result = await this.apiClient.generateTests(code, framework);
            this.updatePanelState('tests', result);
        } catch (error) {
            this.updatePanelState('error', `测试生成失败: ${error}`);
        }
    }

    private async handleLocalAnalysis(code: string): Promise<void> {
        this.updatePanelState('loading', '正在进行本地分析...');

        try {
            const result = this.codeAnalyzer.analyze(code);
            this.updatePanelState('analysis', result);
        } catch (error) {
            this.updatePanelState('error', `本地分析失败: ${error}`);
        }
    }

    private async handleSync(): Promise<void> {
        this.updatePanelState('loading', '正在同步知识库...');

        try {
            await this.apiClient.syncKnowledgeBase();
            this.updatePanelState('info', '知识库同步完成');
        } catch (error) {
            this.updatePanelState('error', `同步失败: ${error}`);
        }
    }

    private showCode(code: string, language: string): void {
        const editor = vscode.window.activeTextEditor;
        if (editor) {
            editor.insertSnippet(
                new vscode.SnippetString(code)
            );
        }
    }

    private updatePanelState(state: string, data: any): void {
        this.panel.webview.postMessage({
            type: 'state',
            state,
            data
        });
    }

    private setInitialContent(): void {
        this.panel.webview.html = this.generateHtml();
    }

    private generateHtml(): string {
        return `<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>C++ AI Assistant</title>
    <style>
        :root {
            --bg-primary: var(--vscode-editor-background);
            --bg-secondary: var(--vscode-editor-inactiveSelectionBackground);
            --text-primary: var(--vscode-editor-foreground);
            --text-secondary: var(--vscode-descriptionForeground);
            --accent: var(--vscode-textLink-foreground);
            --border: var(--vscode-editorLineNumber-foreground);
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            padding: 16px;
            height: 100vh;
            overflow: hidden;
        }

        .container {
            display: flex;
            flex-direction: column;
            height: 100%;
            gap: 16px;
        }

        .header {
            display: flex;
            align-items: center;
            gap: 12px;
            padding-bottom: 16px;
            border-bottom: 1px solid var(--border);
        }

        .header h1 {
            font-size: 18px;
            font-weight: 600;
        }

        .tabs {
            display: flex;
            gap: 8px;
            margin-bottom: 16px;
        }

        .tab {
            padding: 8px 16px;
            border: none;
            background: var(--bg-secondary);
            color: var(--text-primary);
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.2s;
        }

        .tab:hover { background: var(--border); }
        .tab.active { background: var(--accent); color: white; }

        .input-section {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }

        .input-section textarea {
            width: 100%;
            min-height: 150px;
            padding: 12px;
            border: 1px solid var(--border);
            border-radius: 8px;
            background: var(--bg-secondary);
            color: var(--text-primary);
            font-family: 'Fira Code', monospace;
            resize: vertical;
        }

        .input-section button {
            padding: 12px 24px;
            background: var(--accent);
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
            transition: opacity 0.2s;
        }

        .input-section button:hover { opacity: 0.9; }
        .input-section button:disabled { opacity: 0.5; cursor: not-allowed; }

        .output-section {
            flex: 1;
            overflow-y: auto;
            padding: 16px;
            background: var(--bg-secondary);
            border-radius: 8px;
            min-height: 200px;
        }

        .output-section pre {
            white-space: pre-wrap;
            font-family: 'Fira Code', monospace;
            font-size: 13px;
            line-height: 1.6;
        }

        .issue {
            padding: 12px;
            margin: 8px 0;
            border-radius: 6px;
            border-left: 4px solid;
        }

        .issue.critical { border-color: #f14c4c; background: rgba(241, 76, 76, 0.1); }
        .issue.error { border-color: #f88c26; background: rgba(248, 140, 38, 0.1); }
        .issue.warning { border-color: #cca700; background: rgba(204, 167, 0, 0.1); }
        .issue.info { border-color: #3794ff; background: rgba(55, 148, 255, 0.1); }

        .metrics {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 12px;
            margin-bottom: 16px;
        }

        .metric {
            padding: 12px;
            background: var(--bg-secondary);
            border-radius: 8px;
            text-align: center;
        }

        .metric-value { font-size: 24px; font-weight: bold; color: var(--accent); }
        .metric-label { font-size: 12px; color: var(--text-secondary); }

        .loading {
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 40px;
            color: var(--text-secondary);
        }

        .spinner {
            width: 24px;
            height: 24px;
            border: 3px solid var(--border);
            border-top-color: var(--accent);
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-right: 12px;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>C++ AI Assistant</h1>
        </div>

        <div class="tabs">
            <button class="tab active" data-tab="explain">代码解释</button>
            <button class="tab" data-tab="review">代码审查</button>
            <button class="tab" data-tab="refactor">重构建议</button>
            <button class="tab" data-tab="test">生成测试</button>
        </div>

        <div class="input-section">
            <textarea id="codeInput" placeholder="在此粘贴C++代码，或从编辑器选择代码..."></textarea>
            <button id="submitBtn" onclick="handleSubmit()">分析代码</button>
        </div>

        <div class="output-section" id="output">
            <p style="color: var(--text-secondary);">分析结果将显示在这里</p>
        </div>
    </div>

    <script>
        const vscode = acquireVsCodeApi();
        let currentTab = 'explain';

        // Tab切换
        document.querySelectorAll('.tab').forEach(tab => {
            tab.addEventListener('click', () => {
                document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
                tab.classList.add('active');
                currentTab = tab.dataset.tab;
                updateButtonText();
            });
        });

        function updateButtonText() {
            const btn = document.getElementById('submitBtn');
            const texts = {
                explain: '解释代码',
                review: '审查代码',
                refactor: '生成重构建议',
                test: '生成测试'
            };
            btn.textContent = texts[currentTab] || '分析代码';
        }

        function handleSubmit() {
            const code = document.getElementById('codeInput').value;
            if (!code.trim()) {
                alert('请输入代码');
                return;
            }

            showLoading();

            vscode.postMessage({
                type: currentTab,
                code: code,
                language: 'cpp'
            });
        }

        function showLoading() {
            document.getElementById('output').innerHTML = \`
                <div class="loading">
                    <div class="spinner"></div>
                    <span>正在处理...</span>
                </div>
            \`;
        }

        // 处理来自扩展的消息
        window.addEventListener('message', event => {
            const message = event.data;

            if (message.type === 'state') {
                renderOutput(message.state, message.data);
            }
        });

        function renderOutput(state, data) {
            const output = document.getElementById('output');

            switch (state) {
                case 'loading':
                    output.innerHTML = \`
                        <div class="loading">
                            <div class="spinner"></div>
                            <span>\${data}</span>
                        </div>
                    \`;
                    break;

                case 'result':
                    output.innerHTML = \`<pre>\${escapeHtml(data.content || data)}</pre>\`;
                    break;

                case 'review':
                    renderReview(output, data);
                    break;

                case 'tests':
                    renderTests(output, data);
                    break;

                case 'analysis':
                    renderAnalysis(output, data);
                    break;

                case 'error':
                    output.innerHTML = \`<p style="color: #f14c4c;">\${data}</p>\`;
                    break;

                case 'info':
                    output.innerHTML = \`<p style="color: #2d7d2d;">\${data}</p>\`;
                    break;
            }
        }

        function renderReview(output, data) {
            const issues = data.issues || [];
            const score = data.score || 0;

            output.innerHTML = \`
                <div class="metrics">
                    <div class="metric">
                        <div class="metric-value">\${score}</div>
                        <div class="metric-label">代码评分</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">\${issues.length}</div>
                        <div class="metric-label">发现问题</div>
                    </div>
                </div>
                <p>\${data.summary || ''}</p>
                \${issues.map(issue => \`
                    <div class="issue \${issue.severity}">
                        <strong>Line \${issue.line}</strong> [\${issue.category}]
                        <p>\${issue.message}</p>
                        \${issue.suggestion ? \`<p><em>建议: \${issue.suggestion}</em></p>\` : ''}
                    </div>
                \`).join('')}
            \`;
        }

        function renderTests(output, data) {
            const cases = data.testCases || [];

            output.innerHTML = \`
                <p>生成了 \${cases.length} 个测试用例 (\${data.framework})</p>
                \${cases.map(tc => \`
                    <div class="issue info">
                        <strong>\${tc.name}</strong>
                        <p>\${tc.description}</p>
                        <pre>\${escapeHtml(tc.testCode)}</pre>
                    </div>
                \`).join('')}
            \`;
        }

        function renderAnalysis(output, data) {
            const metrics = data.metrics || {};
            const issues = data.issues || [];

            output.innerHTML = \`
                <div class="metrics">
                    <div class="metric">
                        <div class="metric-value">\${metrics.linesOfCode || 0}</div>
                        <div class="metric-label">代码行数</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">\${metrics.cyclomaticComplexity || 0}</div>
                        <div class="metric-label">圈复杂度</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">\${issues.length}</div>
                        <div class="metric-label">发现问题</div>
                    </div>
                </div>
                \${issues.map(issue => \`
                    <div class="issue \${issue.severity}">
                        <strong>Line \${issue.line}</strong> - \${issue.message}
                    </div>
                \`).join('')}
            \`;
        }

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
    </script>
</body>
</html>`;
    }

    public dispose(): void {
        AIAssistantPanel.panels.delete('main');

        this.disposables.forEach(d => d.dispose());
        this.disposables = [];
        this.panel.dispose();
    }
}