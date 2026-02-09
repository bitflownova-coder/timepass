/**
 * Copilot Engine - Security Diagnostics Provider
 * Shows inline security warnings in the editor
 */
import * as vscode from 'vscode';
import { EngineClient, SecurityFinding } from './engineClient';
import { OutputManager } from './outputChannel';
import { getConfig } from './config';

// Quick inline security patterns (runs without engine)
const SECURITY_PATTERNS: { pattern: RegExp; severity: vscode.DiagnosticSeverity; message: string; suggestion: string }[] = [
    // Dangerous functions
    { pattern: /\beval\s*\(/, severity: vscode.DiagnosticSeverity.Error, message: 'Use of eval() is a security risk', suggestion: 'Use JSON.parse() or safer alternatives' },
    { pattern: /\bexec\s*\(/, severity: vscode.DiagnosticSeverity.Warning, message: 'Use of exec() can be dangerous', suggestion: 'Use subprocess with shell=False' },

    // SQL Injection
    { pattern: /f["'].*SELECT.*\{/, severity: vscode.DiagnosticSeverity.Error, message: 'Potential SQL injection via f-string', suggestion: 'Use parameterized queries' },
    { pattern: /["'].*SELECT.*["']\s*\+/, severity: vscode.DiagnosticSeverity.Error, message: 'Potential SQL injection via string concatenation', suggestion: 'Use parameterized queries' },
    { pattern: /\.format\(.*SELECT/i, severity: vscode.DiagnosticSeverity.Error, message: 'Potential SQL injection via .format()', suggestion: 'Use parameterized queries' },
    { pattern: /`.*SELECT.*\$\{/, severity: vscode.DiagnosticSeverity.Error, message: 'Potential SQL injection via template literal', suggestion: 'Use parameterized queries' },

    // Hardcoded secrets
    { pattern: /(?:password|passwd|secret|api_key|apikey|token|auth)\s*=\s*["'][^"']{8,}["']/i, severity: vscode.DiagnosticSeverity.Error, message: 'Possible hardcoded secret detected', suggestion: 'Use environment variables or a secrets manager' },
    { pattern: /(?:AWS_SECRET|PRIVATE_KEY)\s*=\s*["']/i, severity: vscode.DiagnosticSeverity.Error, message: 'Hardcoded cloud credential', suggestion: 'Use environment variables' },

    // JWT without verification
    { pattern: /jwt\.decode\(.*verify\s*=\s*False/i, severity: vscode.DiagnosticSeverity.Error, message: 'JWT decoded without verification', suggestion: 'Set verify=True' },
    { pattern: /jsonwebtoken.*verify.*algorithms.*none/i, severity: vscode.DiagnosticSeverity.Error, message: 'JWT with "none" algorithm allowed', suggestion: 'Specify allowed algorithms explicitly' },

    // Open CORS
    { pattern: /Access-Control-Allow-Origin.*\*/, severity: vscode.DiagnosticSeverity.Warning, message: 'CORS allows all origins', suggestion: 'Restrict to specific origins' },
    { pattern: /allow_origins\s*=\s*\[["']\*["']\]/, severity: vscode.DiagnosticSeverity.Warning, message: 'CORS allows all origins', suggestion: 'Restrict to specific domains' },

    // Weak crypto
    { pattern: /\bmd5\b/i, severity: vscode.DiagnosticSeverity.Warning, message: 'MD5 is cryptographically weak', suggestion: 'Use SHA-256 or bcrypt for passwords' },
    { pattern: /\bsha1\b/i, severity: vscode.DiagnosticSeverity.Warning, message: 'SHA-1 is cryptographically weak', suggestion: 'Use SHA-256 or SHA-3' },

    // Debug/logging issues
    { pattern: /console\.log\(.*password/i, severity: vscode.DiagnosticSeverity.Error, message: 'Password may be logged to console', suggestion: 'Remove sensitive data from logs' },
    { pattern: /print\(.*password/i, severity: vscode.DiagnosticSeverity.Warning, message: 'Password may be printed', suggestion: 'Remove sensitive data from output' },
    { pattern: /DEBUG\s*=\s*True/, severity: vscode.DiagnosticSeverity.Warning, message: 'Debug mode enabled', suggestion: 'Disable debug mode in production' },

    // Unsafe deserialization
    { pattern: /pickle\.loads?\(/, severity: vscode.DiagnosticSeverity.Error, message: 'Pickle deserialization is unsafe with untrusted data', suggestion: 'Use JSON or a safe serialization format' },
    { pattern: /yaml\.load\((?!.*Loader)/, severity: vscode.DiagnosticSeverity.Warning, message: 'yaml.load() without Loader is unsafe', suggestion: 'Use yaml.safe_load()' },
];

export class SecurityDiagnosticsProvider {
    private diagnosticCollection: vscode.DiagnosticCollection;
    private client: EngineClient;
    private output: OutputManager;
    private disposables: vscode.Disposable[] = [];

    constructor(client: EngineClient, output: OutputManager) {
        this.client = client;
        this.output = output;
        this.diagnosticCollection = vscode.languages.createDiagnosticCollection('copilot-engine-security');
    }

    start(): void {
        const config = getConfig();
        if (!config.securityWarnings) { return; }

        // Scan on file open
        const openHandler = vscode.workspace.onDidOpenTextDocument((doc) => {
            this.scanDocument(doc);
        });
        this.disposables.push(openHandler);

        // Scan on file save
        const saveHandler = vscode.workspace.onDidSaveTextDocument((doc) => {
            this.scanDocument(doc);
        });
        this.disposables.push(saveHandler);

        // Scan on file change (debounced)
        let changeTimer: NodeJS.Timeout | null = null;
        const changeHandler = vscode.workspace.onDidChangeTextDocument((e) => {
            if (changeTimer) { clearTimeout(changeTimer); }
            changeTimer = setTimeout(() => {
                this.scanDocument(e.document);
            }, 1500);
        });
        this.disposables.push(changeHandler);

        // Scan all currently open documents
        vscode.workspace.textDocuments.forEach(doc => this.scanDocument(doc));

        this.output.success('Security diagnostics started');
    }

    private scanDocument(document: vscode.TextDocument): void {
        // Only scan code files
        const supportedLanguages = ['python', 'javascript', 'typescript', 'javascriptreact',
            'typescriptreact', 'java', 'go', 'rust', 'ruby', 'php'];
        if (!supportedLanguages.includes(document.languageId)) {
            return;
        }

        // Skip node_modules, venv etc
        const path = document.uri.fsPath;
        if (path.includes('node_modules') || path.includes('site-packages') ||
            path.includes('.venv') || path.includes('__pycache__')) {
            return;
        }

        const diagnostics: vscode.Diagnostic[] = [];
        const text = document.getText();
        const lines = text.split('\n');

        for (let i = 0; i < lines.length; i++) {
            const line = lines[i];

            // Skip comments
            const trimmed = line.trim();
            if (trimmed.startsWith('#') || trimmed.startsWith('//') ||
                trimmed.startsWith('*') || trimmed.startsWith('/*')) {
                continue;
            }

            for (const sp of SECURITY_PATTERNS) {
                if (sp.pattern.test(line)) {
                    const match = line.match(sp.pattern);
                    const startCol = match ? line.indexOf(match[0]) : 0;
                    const endCol = match ? startCol + match[0].length : line.length;

                    const range = new vscode.Range(i, startCol, i, endCol);
                    const diagnostic = new vscode.Diagnostic(range, sp.message, sp.severity);
                    diagnostic.source = 'Copilot Engine';
                    diagnostic.code = {
                        value: 'security',
                        target: vscode.Uri.parse('https://owasp.org/www-project-top-ten/'),
                    };

                    // Add related information
                    diagnostic.relatedInformation = [
                        new vscode.DiagnosticRelatedInformation(
                            new vscode.Location(document.uri, range),
                            `Fix: ${sp.suggestion}`
                        ),
                    ];

                    diagnostics.push(diagnostic);
                }
            }
        }

        this.diagnosticCollection.set(document.uri, diagnostics);
    }

    async scanWorkspace(): Promise<void> {
        const workspacePath = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
        if (!workspacePath) { return; }

        this.output.section('WORKSPACE SECURITY SCAN');
        this.output.info('Scanning all files...');

        try {
            const results = await this.client.scanWorkspaceSecurity(workspacePath);
            if (results.findings && results.findings.length > 0) {
                this.output.warn(`Found ${results.findings.length} security issues:`);
                for (const f of results.findings) {
                    this.output.warn(`  [${f.severity}] ${f.file}:${f.line} - ${f.issue}`);
                }
            } else {
                this.output.success('No security issues found!');
            }
        } catch (err: any) {
            // Fallback: scan open documents only
            this.output.info('Running local pattern scan...');
            let totalIssues = 0;
            for (const doc of vscode.workspace.textDocuments) {
                this.scanDocument(doc);
                const diags = this.diagnosticCollection.get(doc.uri);
                if (diags) { totalIssues += diags.length; }
            }
            this.output.info(`Found ${totalIssues} issues in open files`);
        }
    }

    clearDiagnostics(): void {
        this.diagnosticCollection.clear();
    }

    dispose(): void {
        this.diagnosticCollection.dispose();
        for (const d of this.disposables) { d.dispose(); }
    }
}
