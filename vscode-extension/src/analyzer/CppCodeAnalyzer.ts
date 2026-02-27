/**
 * C++代码分析器 - 本地静态分析
 */
import * as vscode from 'vscode';

export interface AnalysisResult {
    issues: AnalysisIssue[];
    metrics: CodeMetrics;
    entities: CodeEntity[];
}

export interface AnalysisIssue {
    line: number;
    severity: 'critical' | 'error' | 'warning' | 'info';
    category: string;
    message: string;
    suggestion?: string;
    ruleId?: string;
}

export interface CodeMetrics {
    linesOfCode: number;
    cyclomaticComplexity: number;
    commentRatio: number;
    functionCount: number;
    classCount: number;
}

export interface CodeEntity {
    name: string;
    type: 'class' | 'function' | 'method' | 'variable' | 'struct' | 'enum';
    lineStart: number;
    lineEnd: number;
    complexity?: number;
}

export class CppCodeAnalyzer {
    private patterns: Map<RegExp, AnalysisRule>;

    constructor() {
        this.patterns = new Map();
        this.initializePatterns();
    }

    private initializePatterns(): void {
        // 内存安全问题
        this.patterns.set(
            /malloc\s*\(/g,
            {
                severity: 'warning',
                category: 'memory_safety',
                message: 'Raw memory allocation detected',
                suggestion: 'Consider using smart pointers (std::unique_ptr, std::shared_ptr)'
            }
        );

        this.patterns.set(
            /free\s*\(/g,
            {
                severity: 'warning',
                category: 'memory_safety',
                message: 'Raw memory deallocation detected',
                suggestion: 'Ensure proper pairing with malloc() or use RAII'
            }
        );

        this.patterns.set(
            /delete\s+(?!\[)/g,
            {
                severity: 'error',
                category: 'memory_safety',
                message: 'delete used instead of delete[] for potential array',
                suggestion: 'If deleting array, use delete[]'
            }
        );

        this.patterns.set(
            /NULL\b/g,
            {
                severity: 'info',
                category: 'modern_cpp',
                message: 'NULL used instead of nullptr',
                suggestion: 'Use nullptr for type safety'
            }
        );

        // 现代C++问题
        this.patterns.set(
            /auto_ptr/gi,
            {
                severity: 'error',
                category: 'modern_cpp',
                message: 'auto_ptr is deprecated and dangerous',
                suggestion: 'Replace with std::unique_ptr (C++11 or later)'
            }
        );

        this.patterns.set(
            /std::bind\s*\(/g,
            {
                severity: 'info',
                category: 'modern_cpp',
                message: 'std::bind can be replaced with lambdas',
                suggestion: 'Consider using lambda expressions for better readability'
            }
        );

        // 性能问题
        this.patterns.set(
            /vector\.push_back\s*\(\s*.*\.begin\s*\(\)/g,
            {
                severity: 'warning',
                category: 'performance',
                message: 'Inefficient vector operation detected',
                suggestion: 'Use insert() instead of push_back() with iterator'
            }
        );

        this.patterns.set(
            /string\s*\+\s*=/g,
            {
                severity: 'warning',
                category: 'performance',
                message: 'Repeated string concatenation detected',
                suggestion: 'Consider using std::stringstream or std::string::append()'
            }
        );

        // 代码风格
        this.patterns.set(
            /^\s*[a-z_][a-z0-9_]*\s*[A-Z]/gm,
            {
                severity: 'info',
                category: 'readability',
                message: 'Variable name may not follow naming convention',
                suggestion: 'Consider using camelCase or snake_case consistently'
            }
        );
    }

    analyze(code: string): AnalysisResult {
        const issues: AnalysisIssue[] = [];
        const entities: CodeEntity[] = [];

        const lines = code.split('\n');

        // 检测问题
        for (let i = 0; i < lines.length; i++) {
            const line = lines[i];
            const lineNumber = i + 1;

            for (const [pattern, rule] of this.patterns) {
                if (pattern.test(line)) {
                    issues.push({
                        line: lineNumber,
                        severity: rule.severity,
                        category: rule.category,
                        message: rule.message,
                        suggestion: rule.suggestion
                    });
                }
            }

            // 检测函数和类
            this.detectEntities(line, lineNumber, entities);
        }

        // 计算指标
        const metrics = this.calculateMetrics(code, lines, entities);

        return {
            issues,
            metrics,
            entities
        };
    }

    private detectEntities(
        line: string,
        lineNumber: number,
        entities: CodeEntity[]
    ): void {
        // 检测函数定义
        const funcMatch = line.match(/(\w+)\s*\([^)]*\)\s*\{/);
        if (funcMatch && !line.includes('class') && !line.includes('struct')) {
            entities.push({
                name: funcMatch[1],
                type: 'function',
                lineStart: lineNumber,
                lineEnd: lineNumber
            });
        }

        // 检测类定义
        const classMatch = line.match(/\bclass\s+(\w+)/);
        if (classMatch) {
            entities.push({
                name: classMatch[1],
                type: 'class',
                lineStart: lineNumber,
                lineEnd: lineNumber
            });
        }

        // 检测结构体定义
        const structMatch = line.match(/\bstruct\s+(\w+)/);
        if (structMatch) {
            entities.push({
                name: structMatch[1],
                type: 'struct',
                lineStart: lineNumber,
                lineEnd: lineNumber
            });
        }

        // 检测枚举定义
        const enumMatch = line.match(/\benum\s+(?:class\s+)?(\w+)/);
        if (enumMatch) {
            entities.push({
                name: enumMatch[1],
                type: 'enum',
                lineStart: lineNumber,
                lineEnd: lineNumber
            });
        }
    }

    private calculateMetrics(
        code: string,
        lines: string[],
        entities: CodeEntity[]
    ): CodeMetrics {
        // 代码行数
        const linesOfCode = lines.filter(l => l.trim().length > 0).length;

        // 注释比例
        const commentLines = lines.filter(l => 
            l.trim().startsWith('//') || 
            l.trim().startsWith('/*') ||
            l.trim().endsWith('*/')
        ).length;
        const commentRatio = (commentLines / lines.length) * 100;

        // 圈复杂度（简化计算）
        const complexityPatterns = [
            /\bif\b/g, /\belse\b/g, /\bfor\b/g, /\bwhile\b/g,
            /\bcase\b/g, /\bcatch\b/g, /\b\?\s*:/g
        ];
        let cyclomaticComplexity = 1;
        for (const pattern of complexityPatterns) {
            cyclomaticComplexity += (code.match(pattern) || []).length;
        }

        // 统计实体
        const functionCount = entities.filter(e => e.type === 'function' || e.type === 'method').length;
        const classCount = entities.filter(e => e.type === 'class' || e.type === 'struct').length;

        return {
            linesOfCode,
            cyclomaticComplexity,
            commentRatio,
            functionCount,
            classCount
        };
    }

    analyzeFile(document: vscode.TextDocument): AnalysisResult {
        const code = document.getText();
        const result = this.analyze(code);
        
        // 更新实体的结束行
        for (const entity of result.entities) {
            entity.lineEnd = this.findEntityEnd(entity, document);
        }

        return result;
    }

    private findEntityEnd(
        entity: CodeEntity,
        document: vscode.TextDocument
    ): number {
        // 简化实现：查找匹配的右大括号
        const startLine = Math.min(entity.lineStart - 1, document.lineCount - 1);
        let braceCount = 0;
        let foundOpen = false;

        for (let i = startLine; i < document.lineCount; i++) {
            const line = document.lineAt(i).text;
            for (const char of line) {
                if (char === '{') {
                    braceCount++;
                    foundOpen = true;
                } else if (char === '}') {
                    braceCount--;
                    if (foundOpen && braceCount === 0) {
                        return i + 1;
                    }
                }
            }
        }

        return entity.lineEnd;
    }
}

interface AnalysisRule {
    severity: 'critical' | 'error' | 'warning' | 'info';
    category: string;
    message: string;
    suggestion?: string;
}
