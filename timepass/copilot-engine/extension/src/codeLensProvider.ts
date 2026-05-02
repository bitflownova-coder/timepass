/**
 * Copilot Engine - CodeLens Provider
 * Shows inline actions above functions/classes
 */
import * as vscode from 'vscode';
import { EngineClient } from './engineClient';
import { OutputManager } from './outputChannel';
import { getConfig } from './config';

// Language-specific function patterns
const FUNCTION_PATTERNS: Record<string, RegExp[]> = {
    python: [
        /^(\s*)(async\s+)?def\s+(\w+)\s*\(/gm,
        /^(\s*)class\s+(\w+)/gm,
    ],
    javascript: [
        /^(\s*)(async\s+)?function\s+(\w+)\s*\(/gm,
        /^(\s*)(export\s+)?(const|let|var)\s+(\w+)\s*=\s*(async\s+)?\(/gm,
        /^(\s*)(export\s+)?(const|let|var)\s+(\w+)\s*=\s*(async\s+)?function/gm,
        /^(\s*)class\s+(\w+)/gm,
    ],
    typescript: [
        /^(\s*)(async\s+)?function\s+(\w+)\s*[\(<]/gm,
        /^(\s*)(export\s+)?(const|let|var)\s+(\w+)\s*=\s*(async\s+)?\(/gm,
        /^(\s*)(export\s+)?(const|let|var)\s+(\w+)\s*=\s*(async\s+)?function/gm,
        /^(\s*)class\s+(\w+)/gm,
        /^(\s*)(public|private|protected)?\s*(async\s+)?(\w+)\s*\(/gm,
    ],
    java: [
        /^(\s*)(public|private|protected)\s+(static\s+)?\w+\s+(\w+)\s*\(/gm,
        /^(\s*)(public|private|protected)?\s*class\s+(\w+)/gm,
    ],
    go: [
        /^func\s+(\w+)\s*\(/gm,
        /^func\s+\(\w+\s+\*?\w+\)\s+(\w+)\s*\(/gm,
    ],
    rust: [
        /^(\s*)(pub\s+)?(async\s+)?fn\s+(\w+)/gm,
        /^(\s*)(pub\s+)?struct\s+(\w+)/gm,
        /^(\s*)(pub\s+)?impl\s+(\w+)/gm,
    ],
};

const LANGUAGE_MAP: Record<string, string> = {
    'python': 'python',
    'javascript': 'javascript',
    'javascriptreact': 'javascript',
    'typescript': 'typescript',
    'typescriptreact': 'typescript',
    'java': 'java',
    'go': 'go',
    'rust': 'rust',
};

export class CopilotCodeLensProvider implements vscode.CodeLensProvider {
    private client: EngineClient;
    private output: OutputManager;
    private _onDidChangeCodeLenses = new vscode.EventEmitter<void>();
    readonly onDidChangeCodeLenses = this._onDidChangeCodeLenses.event;

    constructor(client: EngineClient, output: OutputManager) {
        this.client = client;
        this.output = output;
    }

    provideCodeLenses(document: vscode.TextDocument): vscode.CodeLens[] {
        const config = getConfig();
        if (!config.codeLensEnabled) { return []; }

        const langId = LANGUAGE_MAP[document.languageId];
        if (!langId) { return []; }

        const patterns = FUNCTION_PATTERNS[langId];
        if (!patterns) { return []; }

        const codeLenses: vscode.CodeLens[] = [];
        const text = document.getText();

        for (const pattern of patterns) {
            // Reset regex
            pattern.lastIndex = 0;
            let match;

            while ((match = pattern.exec(text)) !== null) {
                const line = document.positionAt(match.index).line;
                const range = new vscode.Range(line, 0, line, 0);

                // Extract function name
                const funcName = this.extractFunctionName(match, langId);
                if (!funcName || funcName.startsWith('_') && funcName !== '__init__') {
                    continue;
                }

                // Analyze action
                codeLenses.push(new vscode.CodeLens(range, {
                    title: '🔍 Analyze',
                    command: 'copilotEngine.analyzeFunction',
                    arguments: [document.uri, range, funcName],
                }));

                // Generate Tests action
                codeLenses.push(new vscode.CodeLens(range, {
                    title: '🧪 Test',
                    command: 'copilotEngine.generateTests',
                    arguments: [document.uri, range, funcName],
                }));

                // Security Check action
                codeLenses.push(new vscode.CodeLens(range, {
                    title: '🛡️ Security',
                    command: 'copilotEngine.securityCheckLens',
                    arguments: [document.uri, range, funcName],
                }));

                // Improve action
                codeLenses.push(new vscode.CodeLens(range, {
                    title: '🧠 Improve',
                    command: 'copilotEngine.improveCode',
                    arguments: [document.uri, range, funcName],
                }));

                // Impact action
                codeLenses.push(new vscode.CodeLens(range, {
                    title: '💥 Impact',
                    command: 'copilotEngine.checkImpact',
                    arguments: [document.uri, range, funcName],
                }));
            }
        }

        return codeLenses;
    }

    private extractFunctionName(match: RegExpExecArray, lang: string): string | null {
        // Return the last non-undefined capture group (usually the name)
        for (let i = match.length - 1; i >= 1; i--) {
            if (match[i] && /^\w+$/.test(match[i]) &&
                !['async', 'function', 'const', 'let', 'var', 'export', 'public',
                  'private', 'protected', 'static', 'pub', 'def', 'class', 'func',
                  'fn', 'struct', 'impl'].includes(match[i])) {
                return match[i];
            }
        }
        return null;
    }

    refresh(): void {
        this._onDidChangeCodeLenses.fire();
    }
}

/**
 * Register CodeLens command handlers
 */
export function registerCodeLensCommands(
    context: vscode.ExtensionContext,
    client: EngineClient,
    output: OutputManager
): void {
    // Analyze Function
    context.subscriptions.push(
        vscode.commands.registerCommand('copilotEngine.analyzeFunction',
            async (uri: vscode.Uri, range: vscode.Range, funcName: string) => {
                const doc = await vscode.workspace.openTextDocument(uri);
                const funcCode = extractFunctionBody(doc, range.start.line);
                const workspacePath = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;

                if (!workspacePath) { return; }

                output.show();
                output.section(`ANALYSIS: ${funcName}()`);
                output.info('Analyzing function...');

                try {
                    const result = await client.buildContext(
                        workspacePath,
                        `Analyze this function for bugs, performance issues, and improvement opportunities:\n\n${funcCode}`,
                        doc.uri.fsPath
                    );

                    output.info(result.prompt);
                    output.info(`\nTokens: ${result.token_estimate}`);

                    await vscode.env.clipboard.writeText(result.prompt);
                    vscode.window.showInformationMessage(`Analysis for ${funcName}() copied to clipboard`);
                } catch (err: any) {
                    output.error(`Analysis failed: ${err.message}`);
                }
            }
        )
    );

    // Generate Tests
    context.subscriptions.push(
        vscode.commands.registerCommand('copilotEngine.generateTests',
            async (uri: vscode.Uri, range: vscode.Range, funcName: string) => {
                const doc = await vscode.workspace.openTextDocument(uri);
                const funcCode = extractFunctionBody(doc, range.start.line);
                const workspacePath = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;

                if (!workspacePath) { return; }

                output.show();
                output.section(`TEST GENERATION: ${funcName}()`);

                try {
                    const result = await client.buildContext(
                        workspacePath,
                        `Generate comprehensive unit tests for this function. Include edge cases, error cases, and happy path tests:\n\n${funcCode}`,
                        doc.uri.fsPath
                    );

                    output.info(result.prompt);
                    await vscode.env.clipboard.writeText(result.prompt);
                    vscode.window.showInformationMessage(`Test prompt for ${funcName}() copied to clipboard`);
                } catch (err: any) {
                    output.error(`Test generation failed: ${err.message}`);
                }
            }
        )
    );

    // Security Check
    context.subscriptions.push(
        vscode.commands.registerCommand('copilotEngine.securityCheckLens',
            async (uri: vscode.Uri, range: vscode.Range, funcName: string) => {
                output.show();
                output.section(`SECURITY CHECK: ${funcName}()`);

                try {
                    const findings = await client.scanSecurity(uri.fsPath);
                    if (findings.length === 0) {
                        output.success('No security issues found!');
                        vscode.window.showInformationMessage(`✅ ${funcName}(): No security issues`);
                    } else {
                        for (const f of findings) {
                            output.warn(`[${f.severity}] Line ${f.line}: ${f.issue}`);
                            output.info(`  Fix: ${f.suggestion}`);
                        }
                        vscode.window.showWarningMessage(
                            `⚠️ ${funcName}(): ${findings.length} security issues found`,
                            'View Details'
                        ).then(action => {
                            if (action === 'View Details') { output.show(); }
                        });
                    }
                } catch (err: any) {
                    output.error(`Security check failed: ${err.message}`);
                }
            }
        )
    );

    // Improve Code
    context.subscriptions.push(
        vscode.commands.registerCommand('copilotEngine.improveCode',
            async (uri: vscode.Uri, range: vscode.Range, funcName: string) => {
                const doc = await vscode.workspace.openTextDocument(uri);
                const funcCode = extractFunctionBody(doc, range.start.line);
                const workspacePath = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;

                if (!workspacePath) { return; }

                try {
                    const result = await client.optimizePrompt(
                        workspacePath,
                        `Improve this code for readability, performance, and best practices. Show refactored version with explanation:\n\n${funcCode}`,
                        doc.uri.fsPath
                    );

                    // Inject context comment above the function
                    const editor = await vscode.window.showTextDocument(doc);
                    const insertPos = new vscode.Position(range.start.line, 0);
                    const lang = doc.languageId;
                    const commentStart = lang === 'python' ? '"""' : '/*';
                    const commentEnd = lang === 'python' ? '"""' : '*/';

                    const contextComment = `${commentStart}\nCopilot Context:\n` +
                        `- Task: Improve ${funcName}()\n` +
                        `- Framework: ${result.metadata.project || 'N/A'}\n` +
                        `- Focus: readability, performance, best practices\n` +
                        `${commentEnd}\n`;

                    await editor.edit(editBuilder => {
                        editBuilder.insert(insertPos, contextComment);
                    });

                    vscode.window.showInformationMessage(`Context injected for ${funcName}() - Copilot will see it!`);
                } catch (err: any) {
                    output.error(`Improve failed: ${err.message}`);
                }
            }
        )
    );

    // Check Impact
    context.subscriptions.push(
        vscode.commands.registerCommand('copilotEngine.checkImpact',
            async (uri: vscode.Uri, range: vscode.Range, funcName: string) => {
                const workspacePath = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
                if (!workspacePath) { return; }

                output.show();
                output.section(`IMPACT ANALYSIS: ${funcName}()`);
                output.info('Analyzing change impact...');

                try {
                    const impact = await client.analyzeImpact(workspacePath, uri.fsPath);

                    const riskIcon = impact.risk_level === 'critical' ? '🔴' :
                                     impact.risk_level === 'high' ? '🟠' :
                                     impact.risk_level === 'medium' ? '🟡' : '🟢';

                    output.info(`${riskIcon} Risk: ${impact.risk_level} (${impact.risk_score.toFixed(2)})`);
                    output.info(`Category: ${impact.category}`);

                    if (impact.impact_radius.length > 0) {
                        output.separator();
                        output.info(`Affected files (${impact.impact_radius.length}):`);
                        for (const file of impact.impact_radius) {
                            output.info(`  → ${file}`);
                        }
                    }

                    if (impact.breaking_changes.length > 0) {
                        output.separator();
                        output.warn('Breaking changes:');
                        for (const bc of impact.breaking_changes) {
                            output.warn(`  ! ${bc}`);
                        }
                    }

                    const severity = impact.risk_level === 'critical' || impact.risk_level === 'high'
                        ? `⚠️ ${funcName}(): ${impact.risk_level.toUpperCase()} impact — ${impact.impact_radius.length} files affected`
                        : `✅ ${funcName}(): ${impact.risk_level} impact`;

                    vscode.window.showInformationMessage(severity, 'View Details').then(action => {
                        if (action === 'View Details') { output.show(); }
                    });
                } catch (err: any) {
                    output.error(`Impact analysis failed: ${err.message}`);
                }
            }
        )
    );
}

/**
 * Extract function body from document starting at a line
 */
function extractFunctionBody(doc: vscode.TextDocument, startLine: number): string {
    const lines: string[] = [];
    const startIndent = doc.lineAt(startLine).firstNonWhitespaceCharacterIndex;

    for (let i = startLine; i < Math.min(doc.lineCount, startLine + 100); i++) {
        const line = doc.lineAt(i);
        lines.push(line.text);

        // Stop when we hit a line with same or lesser indentation (next function/class)
        if (i > startLine && line.text.trim().length > 0) {
            const indent = line.firstNonWhitespaceCharacterIndex;
            if (indent <= startIndent && !line.text.trim().startsWith('}') &&
                !line.text.trim().startsWith(')') && !line.text.trim().startsWith(']')) {
                // Check if it's a new definition
                if (/^(\s*)(def |class |function |const |let |var |export |pub |fn |func )/.test(line.text)) {
                    lines.pop();
                    break;
                }
            }
        }
    }

    return lines.join('\n');
}
