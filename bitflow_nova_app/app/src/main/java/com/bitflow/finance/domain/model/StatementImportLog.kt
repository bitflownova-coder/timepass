package com.bitflow.finance.domain.model

import java.time.LocalDate
import java.time.LocalDateTime

data class StatementImportLog(
    val id: Long = 0,
    val accountId: Long,
    val fileName: String,
    val importedAt: LocalDateTime = LocalDateTime.now(),
    val transactionsCount: Int,
    val periodStart: LocalDate?,
    val periodEnd: LocalDate?
)
