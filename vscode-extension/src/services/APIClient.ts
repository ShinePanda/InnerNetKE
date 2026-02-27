/**
 * API客户端服务
 */
import { Configuration } from './Configuration';

export interface APIConfig {
    endpoint: string;
    apiKey: string;
    modelName: string;
    maxTokens: number;
    temperature: number;
}

export interface ReviewResult {
    summary: string;
    score: number;
    issues: ReviewIssue[];
    suggestions: string[];
}

export interface ReviewIssue {
    line: number;
    severity: 'critical' | 'error' | 'warning' | 'info';
    category: string;
    message: string;
    suggestion?: string;
}

export interface RefactorResult {
    currentState: string;
    issues: any[];
    suggestions: RefactorSuggestion[];
    improvements: Record<string, string>;
}

export interface RefactorSuggestion {
    pattern: string;
    description: string;
    beforeCode?: string;
    afterCode?: string;
    benefits: string[];
    risks: string[];
}

export interface TestResult {
    testCases: TestCase[];
    framework: string;
    coverageNotes: string[];
}

export interface TestCase {
    name: string;
    description: string;
    testCode: string;
    expectedBehavior: string;
    edgeCases: string[];
}

export class APIClient {
    private config: Configuration;
    private endpoint: string;
    private headers: Record<string, string>;

    constructor(config: Configuration) {
        this.config = config;
        this.endpoint = config.get<string>('apiEndpoint') || 'http://localhost:8000';
        const apiKey = config.get<string>('apiKey');
        
        this.headers = {
            'Content-Type': 'application/json',
        };
        
        if (apiKey) {
            this.headers['Authorization'] = `Bearer ${apiKey}`;
        }
    }

    private async request<T>(
        endpoint: string,
        method: string,
        body?: any
    ): Promise<T> {
        const url = `${this.endpoint}${endpoint}`;
        
        try {
            const response = await fetch(url, {
                method,
                headers: this.headers,
                body: body ? JSON.stringify(body) : undefined,
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            return (await response.json()) as T;
        } catch (error) {
            console.error(`API request failed: ${endpoint}`, error);
            throw error;
        }
    }

    async explainCode(
        code: string,
        language: string,
        filePath?: string
    ): Promise<string> {
        const result = await this.request<any>('/api/query', 'POST', {
            query: 'Explain this C++ code',
            task_type: 'understanding',
            code,
            language,
            file_path: filePath,
        });
        return result.answer || JSON.stringify(result);
    }

    async reviewCode(
        code: string,
        filePath?: string,
        language: string = 'cpp',
        scope: string = 'full'
    ): Promise<ReviewResult> {
        return this.request<ReviewResult>('/api/review', 'POST', {
            code,
            file_path: filePath,
            language,
            review_scope: scope,
        });
    }

    async refactorCode(
        code: string,
        refactorType: string,
        filePath?: string
    ): Promise<RefactorResult> {
        return this.request<RefactorResult>('/api/refactor', 'POST', {
            code,
            refactor_type: refactorType,
            file_path: filePath,
        });
    }

    async generateTests(
        code: string,
        framework: string = 'gtest',
        coverage: string = 'basic'
    ): Promise<TestResult> {
        return this.request<TestResult>('/api/test', 'POST', {
            code,
            test_framework: framework,
            coverage_level: coverage,
        });
    }

    async analyzeImprovements(code: string): Promise<any> {
        return this.request<any>('/api/query', 'POST', {
            query: 'Suggest improvements for this C++ code',
            task_type: 'refactoring',
            code,
        });
    }

    async syncKnowledgeBase(): Promise<void> {
        await this.request('/api/index/rebuild', 'POST');
    }

    async getStats(): Promise<any> {
        return this.request('/api/index/stats', 'GET');
    }

    async checkHealth(): Promise<boolean> {
        try {
            const response = await fetch(`${this.endpoint}/health`);
            return response.ok;
        } catch {
            return false;
        }
    }
}