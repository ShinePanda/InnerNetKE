/**
 * 代码Lens提供者 - 在编辑器中显示AI建议
 */
import * as vscode from 'vscode';
import { APIClient } from '../services/APIClient';
import { CppCodeAnalyzer } from '../analyzer/CppCodeAnalyzer';

export class CodeLensProvider implements vscode.CodeLensProvider<vscode.CodeLens> {
    private apiClient: APIClient;
    private codeAnalyzer: CppCodeAnalyzer;
    private _onDidChangeCodeLenses: vscode.EventEmitter<void>;

    constructor(apiClient: APIClient, codeAnalyzer: CppCodeAnalyzer) {
        this.apiClient = apiClient;
        this.codeAnalyzer = codeAnalyzer;
        this._onDidChangeCodeLenses = new vscode.EventEmitter<void>();
    }

    get onDidChangeCodeLenses(): vscode.Event<void> {
        return this._onDidChangeCodeLenses.event;
    }

    provideCodeLenses(
        document: vscode.TextDocument,
        token: vscode.CancellationToken
    ): vscode.ProviderResult<vscode.CodeLens[]> {
        const lenses: vscode.CodeLens[] = [];

        // 只对C++文件提供CodeLens
        if (!this.isCppFile(document)) {
            return lenses;
        }

        try {
            // 分析代码问题
            const issues = this.codeAnalyzer.analyze(document.getText());
            
            // 为每个问题添加CodeLens
            for (const issue of issues.issues || []) {
                const line = document.lineAt(issue.line - 1);
                const range = new vscode.Range(
                    line.range.start,
                    line.range.end
                );

                const lens = new vscode.CodeLens(range, {
                    title: this.getIssueIcon(issue.severity),
                    command: 'cppAIAssistant.reviewCode',
                    arguments: []
                });

                lenses.push(lens);
            }

            // 添加分析整个文件的CodeLens
            if (lenses.length > 0) {
                const lastLine = document.lineAt(document.lineCount - 1);
                const range = new vscode.Range(
                    new vscode.Position(0, 0),
                    lastLine.range.end
                );

                lenses.push(
                    new vscode.CodeLens(range, {
                        title: `$(lightbulb) AI审查 (${issues.issues?.length || 0} 问题)`,
                        command: 'cppAIAssistant.reviewCode',
                        arguments: []
                    })
                );
            }

        } catch (error) {
            console.error('CodeLens analysis failed:', error);
        }

        return lenses;
    }

    private isCppFile(document: vscode.TextDocument): boolean {
        const ext = document.fileName.split('.').pop()?.toLowerCase();
        return ['cpp', 'c', 'h', 'hpp', 'cc', 'cxx'].includes(ext || '');
    }

    private getIssueIcon(severity: string): string {
        switch (severity) {
            case 'critical':
                return '$(error) 严重';
            case 'error':
                return '$(close) 错误';
            case 'warning':
                return '$(warning) 警告';
            case 'info':
                return '$(info) 信息';
            default:
                return '$(question) 问题';
        }
    }
}

interface Issue {
    line: number;
    severity: string;
    category: string;
    message: string;
}