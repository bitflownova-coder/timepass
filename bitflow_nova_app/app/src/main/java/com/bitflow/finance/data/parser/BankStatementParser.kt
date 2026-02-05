package com.bitflow.finance.data.parser

import com.bitflow.finance.domain.model.ActivityType
import java.io.InputStream
import java.time.LocalDate

/**
 * Interface for parsing bank statements from different formats
 */
interface BankStatementParser {
    /**
     * Parse transactions from an input stream
     * @param inputStream The statement file input stream
     * @return ParseResult containing transactions and detected current balance
     */
    fun parse(inputStream: InputStream): ParseResult
    
    /**
     * Get the name of this parser for logging/debugging
     */
    fun getParserName(): String
}

/**
 * Exception thrown when statement format cannot be determined
 */
class UnknownStatementFormatException(message: String) : Exception(message)

/**
 * Exception thrown when parsing fails
 */
class StatementParsingException(message: String, cause: Throwable? = null) : Exception(message, cause)
