/**
 * C++ AI Assistant - VSCode Extension
 * AI-powered C++ code refactoring and programming assistant
 */
import * as vscode from 'vscode';
import { AIAssistantPanel } from './panels/AIAssistantPanel';
import { CodeLensProvider } from './providers/CodeLensProvider';
import { CppCodeAnalyzer } from './analyzer/CppCodeAnalyzer';
import { APIClient } from './services/APIClient';
import { Configuration } from './services/Configuration';

export function activate(context: vscode.ExtensionContext): void {
    console.log('C++ AI Assistant is now active');

    // 初始化配置
    const config = new Configuration(context);

    // 初始化API客户端
    const apiClient = new APIClient(config);

    // 初始化代码分析器
    const codeAnalyzer = new CppCodeAnalyzer();

    // 注册代码Lens提供者
    const codeLensProvider = new CodeLensProvider(apiClient, codeAnalyzer);
    context.subscriptions.push(
        vscode.languages.registerCodeLensProvider(
            [{ scheme: 'file', language: 'cpp' }, { scheme: 'file', language: 'c' }, { scheme: 'file', language: 'h' }, { scheme: 'file', language: 'hpp' }],
            codeLensProvider
        )
    );

    // 注册命令
    registerCommands(context, apiClient, codeAnalyzer, config);

    // 创建状态栏
    createStatusBar(context, apiClient);

    // 创建侧边面板
    createWebviewPanels(context, apiClient, codeAnalyzer, config);
}

function registerCommands(
    context: vscode.ExtensionContext,
    apiClient: APIClient,
    codeAnalyzer: CppCodeAnalyzer,
    config: Configuration
): void {
    // 解释选中代码
    context.subscriptions.push(
        vscode.commands.registerCommand('cppAIAssistant.explainCode', async () => {
            const editor = vscode.window.activeTextEditor;
            if (!editor) {
                vscode.window.showErrorMessage('No active editor');
                return;
            }

            const selection = editor.document.getText(editor.selection);
            if (!selection) {
                vscode.window.showErrorMessage('Please select code to explain');
                return;
            }

            try {
                const result = await apiClient.explainCode(
                    selection,
                    editor.document.languageId,
                    editor.document.uri.fsPath
                );
                showResultInPanel('Code Explanation', result, context);
            } catch (error) {
                vscode.window.showErrorMessage(`Explanation failed: ${error}`);
            }
        })
    );

    // 重构选中代码
    context.subscriptions.push(
        vscode.commands.registerCommand('cppAIAssistant.refactorCode', async () => {
            const editor = vscode.window.activeTextEditor;
            if (!editor) {
                vscode.window.showErrorMessage('No active editor');
                return;
            }

            const selection = editor.document.getText(editor.selection);
            if (!selection) {
                vscode.window.showErrorMessage('Please select code to refactor');
                return;
            }

            const refactorType = await vscode.window.showQuickPick(
                ['extract-method', 'inline-method', 'rename', 'simplify-conditionals', 'modern-cpp'].map(label => ({ label })),
                { placeHolder: 'Select refactoring type' }
            );

            if (!refactorType) return;

            try {
                const result = await apiClient.refactorCode(
                    selection,
                    refactorType.label,
                    editor.document.uri.fsPath
                );
                showResultInPanel('Refactoring Suggestions', JSON.stringify(result, null, 2), context);
            } catch (error) {
                vscode.window.showErrorMessage(`Refactoring failed: ${error}`);
            }
        })
    );

    // 审查当前文件
    context.subscriptions.push(
        vscode.commands.registerCommand('cppAIAssistant.reviewCode', async () => {
            const editor = vscode.window.activeTextEditor;
            if (!editor) {
                vscode.window.showErrorMessage('No active editor');
                return;
            }

            const content = editor.document.getText();
            const uri = editor.document.uri;

            try {
                const result = await apiClient.reviewCode(
                    content,
                    uri.fsPath,
                    editor.document.languageId
                );
                showReviewResults(result, context);
            } catch (error) {
                vscode.window.showErrorMessage(`Code review failed: ${error}`);
            }
        })
    );

    // 生成单元测试
    context.subscriptions.push(
        vscode.commands.registerCommand('cppAIAssistant.generateTests', async () => {
            const editor = vscode.window.activeTextEditor;
            if (!editor) {
                vscode.window.showErrorMessage('No active editor');
                return;
            }

            const selection = editor.document.getText(editor.selection);
            const content = selection || editor.document.getText();

            const framework = await vscode.window.showQuickPick(
                ['gtest', 'catch2', 'doctest'].map(label => ({ label })),
                { placeHolder: 'Select test framework' }
            );

            if (!framework) return;

            try {
                const result = await apiClient.generateTests(content, framework.label);
                showTestResults(result, context);
            } catch (error) {
                vscode.window.showErrorMessage(`Test generation failed: ${error}`);
            }
        })
    );

    // 建议改进
    context.subscriptions.push(
        vscode.commands.registerCommand('cppAIAssistant.suggestImprovements', async () => {
            const editor = vscode.window.activeTextEditor;
            if (!editor) {
                vscode.window.showErrorMessage('No active editor');
                return;
            }

            const selection = editor.document.getText(editor.selection);
            const content = selection || editor.document.getText();

            try {
                const result = await apiClient.analyzeImprovements(content);
                showResultInPanel('Improvement Suggestions', result, context);
            } catch (error) {
                vscode.window.showErrorMessage(`Analysis failed: ${error}`);
            }
        })
    );

    // 打开AI助手面板
    context.subscriptions.push(
        vscode.commands.registerCommand('cppAIAssistant.openPanel', () => {
            AIAssistantPanel.createOrShow(context.extensionUri, apiClient);
        })
    );

    // 同步知识库
    context.subscriptions.push(
        vscode.commands.registerCommand('cppAIAssistant.syncKnowledgeBase', async () => {
            try {
                await apiClient.syncKnowledgeBase();
                vscode.window.showInformationMessage('Knowledge base sync started');
            } catch (error) {
                vscode.window.showErrorMessage(`Sync failed: ${error}`);
            }
        })
    );

    // 分析当前文件
    context.subscriptions.push(
        vscode.commands.registerCommand('cppAIAssistant.analyzeFile', async () => {
            const editor = vscode.window.activeTextEditor;
            if (!editor) {
                vscode.window.showErrorMessage('No active editor');
                return;
            }

            const content = editor.document.getText();
            const result = codeAnalyzer.analyze(content);
            
            showResultInPanel('Code Analysis', JSON.stringify(result, null, 2), context);
        })
    );
}

function createStatusBar(
    context: vscode.ExtensionContext,
    apiClient: APIClient
): void {
    const statusBar = vscode.window.createStatusBarItem(
        vscode.StatusBarAlignment.Right,
        100
    );
    statusBar.text = '$(sparkle) C++ AI';
    statusBar.tooltip = 'C++ AI Assistant - Click to open';
    statusBar.command = 'cppAIAssistant.openPanel';
    statusBar.show();
    context.subscriptions.push(statusBar);
}

function createWebviewPanels(
    context: vscode.ExtensionContext,
    apiClient: APIClient,
    codeAnalyzer: CppCodeAnalyzer,
    config: Configuration
): void {
    context.subscriptions.push(
        vscode.window.registerWebviewPanelSerializer(
            AIAssistantPanel.viewType,
            {
                async deserializeWebviewPanel(panel: vscode.WebviewPanel, state: any): Promise<void> {
                    // 恢复面板状态
                }
            }
        )
    );
}

function showResultInPanel(
    title: string,
    result: string,
    context: vscode.ExtensionContext
): void {
    const panel = vscode.window.createWebviewPanel(
        'cppAIResult',
        title,
        vscode.ViewColumn.Two,
        { enableScripts: true }
    );

    panel.webview.html = generateWebviewContent(title, result);
}

function showReviewResults(
    result: any,
    context: vscode.ExtensionContext
): void {
    const panel = vscode.window.createWebviewPanel(
        'cppAIReview',
        'Code Review Results',
        vscode.ViewColumn.Two,
        { enableScripts: true }
    );

    const html = generateReviewResultsHTML(result);
    panel.webview.html = html;
}

function showTestResults(
    result: any,
    context: vscode.ExtensionContext
): void {
    const panel = vscode.window.createWebviewPanel(
        'cppAITests',
        'Generated Tests',
        vscode.ViewColumn.Two,
        { enableScripts: true }
    );

    const html = generateTestResultsHTML(result);
    panel.webview.html = html;
}

function generateWebviewContent(title: string, content: string): string {
    return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>${title}</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            padding: 20px;
            background-color: var(--vscode-editor-background);
            color: var(--vscode-editor-foreground);
        }
        pre {
            background-color: var(--vscode-editor-inactiveSelectionBackground);
            padding: 16px;
            border-radius: 8px;
            overflow-x: auto;
        }
        code {
            font-family: 'Fira Code', 'Cascadia Code', Consolas, monospace;
        }
    </style>
</head>
<body>
    <h1>${title}</h1>
    <pre><code>${escapeHtml(content)}</code></pre>
</body>
</html>`;
}

function generateReviewResultsHTML(result: any): string {
    const issues = result.issues || [];
    const score = result.score || 0;
    
    return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Code Review Results</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            padding: 20px;
            background-color: var(--vscode-editor-background);
            color: var(--vscode-editor-foreground);
        }
        .score {
            font-size: 48px;
            font-weight: bold;
            text-align: center;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        .score-high { background-color: #2d7d2d; }
        .score-medium { background-color: #7d7d2d; }
        .score-low { background-color: #7d2d2d; }
        .issue {
            padding: 12px;
            margin: 8px 0;
            border-radius: 6px;
            border-left: 4px solid;
        }
        .critical { border-color: #f14c4c; background: rgba(241, 76, 76, 0.1); }
        .error { border-color: #f88c26; background: rgba(248, 140, 38, 0.1); }
        .warning { border-color: #cca700; background: rgba(204, 167, 0, 0.1); }
        .info { border-color: #3794ff; background: rgba(55, 148, 255, 0.1); }
        .line { color: var(--vscode-symbolIcon-keywordTargetForeground); }
        .message { margin: 4px 0; }
        .suggestion { 
            color: var(--vscode-textLink-foreground);
            font-style: italic;
        }
        pre {
            background: var(--vscode-editor-inactiveSelectionBackground);
            padding: 12px;
            border-radius: 6px;
            overflow-x: auto;
        }
    </style>
</head>
<body>
    <h1>Code Review Results</h1>
    <div class="score ${score >= 80 ? 'score-high' : score >= 50 ? 'score-medium' : 'score-low'}">
        Score: ${score}/100
    </div>
    
    <h2>Summary</h2>
    <p>${result.summary || 'No summary available'}</p>
    
    <h2>Issues Found (${issues.length})</h2>
    ${issues.map((issue: any) => `
        <div class="issue ${issue.severity}">
            <div class="line">Line ${issue.line}: ${issue.category}</div>
            <div class="message">${issue.message}</div>
            ${issue.suggestion ? `<div class="suggestion">Suggestion: ${issue.suggestion}</div>` : ''}
        </div>
    `).join('')}
    
    ${result.suggestions && result.suggestions.length > 0 ? `
        <h2>General Suggestions</h2>
        <ul>
            ${result.suggestions.map((s: string) => `<li>${s}</li>`).join('')}
        </ul>
    ` : ''}
</body>
</html>`;
}

function generateTestResultsHTML(result: any): string {
    const testCases = result.test_cases || [];
    
    return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Generated Tests</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            padding: 20px;
            background-color: var(--vscode-editor-background);
            color: var(--vscode-editor-foreground);
        }
        h2 { border-bottom: 1px solid var(--vscode-editorLineNumber-foreground); }
        .test-case {
            background: var(--vscode-editor-inactiveSelectionBackground);
            padding: 16px;
            margin: 16px 0;
            border-radius: 8px;
        }
        .test-name { font-weight: bold; color: var(--vscode-symbolIcon-functionForeground); }
        .description { color: var(--vscode-descriptionForeground); margin: 8px 0; }
        pre {
            background: var(--vscode-editor-background);
            padding: 12px;
            border-radius: 6px;
            overflow-x: auto;
        }
        .framework-badge {
            display: inline-block;
            padding: 4px 8px;
            background: var(--vscode-symbolIcon-classForeground);
            border-radius: 4px;
            font-size: 12px;
            margin-bottom: 16px;
        }
    </style>
</head>
<body>
    <h1>Generated Tests</h1>
    <div class="framework-badge">Framework: ${result.framework || 'gtest'}</div>
    
    <p>Total test cases: ${testCases.length}</p>
    
    ${testCases.map((tc: any) => `
        <div class="test-case">
            <div class="test-name">${tc.name}</div>
            <div class="description">${tc.description}</div>
            <pre><code>${escapeHtml(tc.test_code)}</code></pre>
            ${tc.edge_cases && tc.edge_cases.length > 0 ? `
                <h4>Edge Cases Covered:</h4>
                <ul>
                    ${tc.edge_cases.map((ec: string) => `<li>${ec}</li>`).join('')}
                </ul>
            ` : ''}
        </div>
    `).join('')}
</body>
</html>`;
}

function escapeHtml(text: string): string {
    return text
        .replace(/&/g, '&')
        .replace(/</g, '<')
        .replace(/>/g, '>')
        .replace(/"/g, '"')
        .replace(/'/g, '&#039;');
}

export function deactivate(): void {
    console.log('C++ AI Assistant is now deactivated');
}