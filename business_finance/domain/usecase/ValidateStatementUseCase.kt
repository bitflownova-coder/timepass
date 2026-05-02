package com.bitflow.finance.domain.usecase

import java.io.InputStream
import javax.inject.Inject

/**
 * Validates bank statement files before importing
 */
class ValidateStatementUseCase @Inject constructor() {
    
    data class ValidationResult(
        val isValid: Boolean,
        val fileFormat: FileFormat?,
        val errorMessage: String? = null,
        val estimatedTransactions: Int = 0
    )
    
    enum class FileFormat {
        CSV, TSV, XLS, XLSX, PDF, UNKNOWN
    }
    
    operator fun invoke(fileName: String, fileSize: Long): ValidationResult {
        // Check file size (max 10MB)
        if (fileSize > 10 * 1024 * 1024) {
            return ValidationResult(
                isValid = false,
                fileFormat = null,
                errorMessage = "File size exceeds 10MB limit"
            )
        }
        
        // Check file size (min 100 bytes)
        if (fileSize < 100) {
            return ValidationResult(
                isValid = false,
                fileFormat = null,
                errorMessage = "File is too small to be a valid statement"
            )
        }
        
        // Detect format from extension
        val format = when {
            fileName.endsWith(".csv", ignoreCase = true) -> FileFormat.CSV
            fileName.endsWith(".tsv", ignoreCase = true) -> FileFormat.TSV
            fileName.endsWith(".xls", ignoreCase = true) -> FileFormat.XLS
            fileName.endsWith(".xlsx", ignoreCase = true) -> FileFormat.XLSX
            fileName.endsWith(".pdf", ignoreCase = true) -> FileFormat.PDF
            else -> FileFormat.UNKNOWN
        }
        
        if (format == FileFormat.UNKNOWN) {
            return ValidationResult(
                isValid = false,
                fileFormat = null,
                errorMessage = "Unsupported file format. Please use CSV, TSV, XLS, XLSX, or PDF"
            )
        }
        
        return ValidationResult(
            isValid = true,
            fileFormat = format,
            errorMessage = null
        )
    }
}
