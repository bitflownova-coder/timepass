package com.bitflow.finance.data.parser

/**
 * Utility functions for parsing CSV data that may contain quoted fields
 */
object CsvUtils {
    
    /**
     * Parse a CSV line handling quoted fields that may contain commas
     * 
     * Example:
     *   Input: 2025-04-20,"36,000.00",Description
     *   Output: [2025-04-20, 36,000.00, Description]
     *   
     * @param line CSV line to parse
     * @param delimiter The delimiter character (default: comma)
     * @return List of field values with quotes and extra whitespace removed
     */
    fun parseCsvLine(line: String, delimiter: Char = ','): List<String> {
        val fields = mutableListOf<String>()
        val currentField = StringBuilder()
        var inQuotes = false
        var i = 0
        
        while (i < line.length) {
            val char = line[i]
            
            when {
                // Handle quote character
                char == '"' -> {
                    if (inQuotes && i + 1 < line.length && line[i + 1] == '"') {
                        // Escaped quote (two consecutive quotes)
                        currentField.append('"')
                        i++ // Skip next quote
                    } else {
                        // Toggle quote mode
                        inQuotes = !inQuotes
                    }
                }
                
                // Handle delimiter
                char == delimiter && !inQuotes -> {
                    fields.add(currentField.toString().trim())
                    currentField.clear()
                }
                
                // Regular character
                else -> {
                    currentField.append(char)
                }
            }
            
            i++
        }
        
        // Add last field
        fields.add(currentField.toString().trim())
        
        return fields
    }
    
    /**
     * Split CSV/TSV line with auto-detection of delimiter
     * 
     * Detects tabs vs commas and uses appropriate delimiter.
     * If line contains quotes, uses proper CSV parsing.
     */
    fun splitCsvLine(line: String): List<String> {
        // Auto-detect delimiter: prefer tab when present, fallback to comma
        val tabCount = line.count { it == '\t' }
        val commaCount = line.count { it == ',' }
        
        val delimiter = when {
            tabCount > 0 && tabCount >= commaCount -> '\t'  // Tab-separated
            else -> ','  // Comma-separated (default)
        }
        
        // If line contains quotes, use proper CSV parsing with detected delimiter
        return if (line.contains('"')) {
            parseCsvLine(line, delimiter)
        } else {
            // Simple split for non-quoted lines
            line.split(delimiter).map { it.trim() }
        }
    }
}
