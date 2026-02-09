"""
Copilot Engine - SQL Analyzer
Validates SQL queries for common issues, injection risks,
performance problems, and missing best practices.
"""
import re
from typing import Optional


class SQLAnalyzer:
    """Analyzes SQL queries for issues and optimization opportunities."""

    # Dangerous SQL patterns
    INJECTION_PATTERNS = [
        (r'["\'].*\+.*["\']', 'String concatenation in SQL - injection risk'),
        (r'\{.*\}', 'Variable interpolation in SQL - injection risk'),
        (r'%s|%d', 'Old-style formatting - prefer parameterized queries'),
        (r'\.format\(', '.format() in SQL - injection risk'),
        (r'f["\']', 'f-string in SQL - injection risk'),
    ]

    # Performance anti-patterns
    PERFORMANCE_PATTERNS = [
        (r'SELECT\s+\*', 'SELECT * fetches all columns - specify only needed columns'),
        (r'SELECT.*(?:(?!LIMIT).)*$', 'Missing LIMIT clause - may return too many rows', True),
        (r'NOT\s+IN\s*\(', 'NOT IN can be slow - consider LEFT JOIN or NOT EXISTS'),
        (r'LIKE\s+["\']%', 'Leading wildcard in LIKE prevents index usage'),
        (r'OR\s+', 'Multiple OR conditions - consider using IN or UNION'),
        (r'ORDER\s+BY\s+RAND', 'ORDER BY RAND() is extremely slow on large tables'),
        (r'(?:COUNT|SUM|AVG|MAX|MIN)\s*\(\s*\*\s*\)', None, False),  # COUNT(*) is fine
        (r'DISTINCT', 'DISTINCT may indicate a query design issue'),
        (r'HAVING\s+COUNT', None, False),  # Common pattern, ok
    ]

    # Missing best practices
    BEST_PRACTICE_CHECKS = [
        (r'DELETE\s+FROM\s+\w+\s*$', 'DELETE without WHERE clause - will delete all rows!'),
        (r'UPDATE\s+\w+\s+SET.*(?:(?!WHERE).)*$', 'UPDATE without WHERE clause - will update all rows!'),
        (r'DROP\s+TABLE\s+(?!IF\s+EXISTS)', 'Use DROP TABLE IF EXISTS for safety'),
        (r'CREATE\s+TABLE\s+(?!IF\s+NOT\s+EXISTS)', 'Use CREATE TABLE IF NOT EXISTS for safety'),
        (r'TRUNCATE\s+TABLE', 'TRUNCATE is irreversible - consider DELETE with WHERE instead'),
        (r'ALTER\s+TABLE.*DROP\s+COLUMN', 'Dropping column is irreversible - ensure backup exists'),
    ]

    def analyze(self, query: str, workspace_path: Optional[str] = None) -> dict:
        """Full SQL query analysis."""
        query_normalized = ' '.join(query.strip().split())
        findings = []

        # Check for injection risks
        for pattern, message in self.INJECTION_PATTERNS:
            if re.search(pattern, query, re.IGNORECASE):
                findings.append({
                    'category': 'injection',
                    'severity': 'HIGH',
                    'message': message,
                    'suggestion': 'Use parameterized queries with placeholders (?, :name, $1)',
                })

        # Check for performance issues
        for item in self.PERFORMANCE_PATTERNS:
            pattern, message = item[0], item[1]
            if message is None:
                continue
            is_multiline = item[2] if len(item) > 2 else False

            flags = re.IGNORECASE | (re.DOTALL if is_multiline else 0)
            if re.search(pattern, query_normalized, flags):
                findings.append({
                    'category': 'performance',
                    'severity': 'MEDIUM',
                    'message': message,
                    'suggestion': self._get_perf_suggestion(pattern),
                })

        # Check best practices
        for pattern, message in self.BEST_PRACTICE_CHECKS:
            if re.search(pattern, query_normalized, re.IGNORECASE):
                findings.append({
                    'category': 'best_practice',
                    'severity': 'HIGH',
                    'message': message,
                    'suggestion': 'Add appropriate safety clauses',
                })

        # Determine query type
        query_type = self._detect_query_type(query_normalized)

        # Estimate complexity
        complexity = self._estimate_complexity(query_normalized)

        return {
            'query': query[:500],
            'query_type': query_type,
            'complexity': complexity,
            'total_issues': len(findings),
            'findings': findings,
            'is_safe': len([f for f in findings if f['severity'] == 'HIGH']) == 0,
            'optimized_query': self._suggest_optimization(query_normalized) if findings else None,
        }

    def validate_query_syntax(self, query: str) -> dict:
        """Basic SQL syntax validation."""
        errors = []
        query_clean = query.strip()

        # Check for balanced parentheses
        open_count = query_clean.count('(')
        close_count = query_clean.count(')')
        if open_count != close_count:
            errors.append(f'Unbalanced parentheses: {open_count} open, {close_count} close')

        # Check for balanced quotes
        single_quotes = query_clean.count("'") - query_clean.count("\\'")
        if single_quotes % 2 != 0:
            errors.append('Unbalanced single quotes')

        double_quotes = query_clean.count('"') - query_clean.count('\\"')
        if double_quotes % 2 != 0:
            errors.append('Unbalanced double quotes')

        # Check for common missing keywords
        upper = query_clean.upper()
        if 'SELECT' in upper and 'FROM' not in upper and 'DUAL' not in upper:
            if not re.search(r'SELECT\s+\d|SELECT\s+[\'"]|SELECT\s+NOW|SELECT\s+VERSION', upper):
                errors.append('SELECT without FROM clause')

        if 'INSERT' in upper and 'INTO' not in upper:
            errors.append('INSERT without INTO')

        if 'JOIN' in upper and 'ON' not in upper and 'USING' not in upper:
            if 'NATURAL' not in upper and 'CROSS' not in upper:
                errors.append('JOIN without ON or USING clause')

        return {
            'valid': len(errors) == 0,
            'errors': errors,
        }

    def _detect_query_type(self, query: str) -> str:
        """Detect the type of SQL query."""
        upper = query.upper().strip()
        if upper.startswith('SELECT'):
            return 'SELECT'
        elif upper.startswith('INSERT'):
            return 'INSERT'
        elif upper.startswith('UPDATE'):
            return 'UPDATE'
        elif upper.startswith('DELETE'):
            return 'DELETE'
        elif upper.startswith('CREATE'):
            return 'DDL'
        elif upper.startswith('ALTER'):
            return 'DDL'
        elif upper.startswith('DROP'):
            return 'DDL'
        else:
            return 'OTHER'

    def _estimate_complexity(self, query: str) -> str:
        """Estimate query complexity."""
        upper = query.upper()
        score = 0

        # Count joins
        joins = len(re.findall(r'\bJOIN\b', upper))
        score += joins * 2

        # Count subqueries
        subqueries = upper.count('SELECT') - 1
        score += subqueries * 3

        # Count aggregate functions
        aggs = len(re.findall(r'\b(COUNT|SUM|AVG|MAX|MIN|GROUP_CONCAT)\b', upper))
        score += aggs

        # Count conditions
        conditions = len(re.findall(r'\b(AND|OR)\b', upper))
        score += conditions

        if upper.count('GROUP BY'):
            score += 2
        if upper.count('HAVING'):
            score += 2
        if upper.count('UNION'):
            score += 3

        if score >= 10:
            return 'complex'
        elif score >= 5:
            return 'moderate'
        else:
            return 'simple'

    def _suggest_optimization(self, query: str) -> Optional[str]:
        """Suggest an optimized version of the query."""
        optimized = query

        # Replace SELECT * with note
        if re.search(r'SELECT\s+\*', optimized, re.IGNORECASE):
            optimized = re.sub(
                r'SELECT\s+\*',
                'SELECT /* specify columns */ *',
                optimized,
                flags=re.IGNORECASE
            )

        return optimized if optimized != query else None

    def _get_perf_suggestion(self, pattern: str) -> str:
        """Get performance improvement suggestion."""
        suggestions = {
            r'SELECT\s+\*': 'List only the columns you need to reduce I/O',
            r'NOT\s+IN': 'Rewrite as LEFT JOIN ... WHERE ... IS NULL',
            r'LIKE\s+["\']%': 'Consider full-text search or reverse the column for suffix matching',
            r'OR\s+': 'Consider using IN (...) or UNION ALL for better index usage',
            r'ORDER\s+BY\s+RAND': 'Use a subquery with random offset: WHERE id >= (SELECT FLOOR(RAND() * MAX(id)) FROM table) LIMIT 1',
            r'DISTINCT': 'Review if the JOIN conditions produce duplicates; fix the query logic instead',
        }
        for p, s in suggestions.items():
            if re.search(p, pattern, re.IGNORECASE):
                return s
        return 'Review query for optimization opportunities'
