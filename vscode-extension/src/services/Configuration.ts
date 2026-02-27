/**
 * 配置管理服务
 */
import * as vscode from 'vscode';

export class Configuration {
    private context: vscode.ExtensionContext;
    private readonly section = 'cppAIAssistant';

    constructor(context: vscode.ExtensionContext) {
        this.context = context;
    }

    get<T>(key: string): T | undefined {
        const config = vscode.workspace.getConfiguration(this.section);
        return config.get<T>(key);
    }

    set(key: string, value: any): Thenable<void> {
        const config = vscode.workspace.getConfiguration(this.section);
        return config.update(key, value, vscode.ConfigurationTarget.Global);
    }

    getApiEndpoint(): string {
        return this.get<string>('apiEndpoint') || 'http://localhost:8000';
    }

    getApiKey(): string {
        return this.get<string>('apiKey') || '';
    }

    getModelName(): string {
        return this.get<string>('modelName') || 'qwen-3-235b';
    }

    getMaxTokens(): number {
        return this.get<number>('maxTokens') || 8192;
    }

    getTemperature(): number {
        return this.get<number>('temperature') || 0.1;
    }

    isAutoReviewEnabled(): boolean {
        return this.get<boolean>('autoReviewOnSave') || false;
    }

    isSyntaxHighlightingEnabled(): boolean {
        return this.get<boolean>('enableSyntaxHighlighting') !== false;
    }
}
