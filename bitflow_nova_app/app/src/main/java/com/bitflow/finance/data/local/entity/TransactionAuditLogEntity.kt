package com.bitflow.finance.data.local.entity

import androidx.room.Entity
import androidx.room.PrimaryKey
import java.time.LocalDateTime

enum class AuditAction {
    CREATE, UPDATE, DELETE
}

@Entity(
    tableName = "transaction_audit_logs",
    indices = [
        androidx.room.Index(value = ["transactionId"]),
        androidx.room.Index(value = ["userId"])
    ]
)
data class TransactionAuditLogEntity(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    val transactionId: Long,
    val userId: String, // Who made the change
    val action: AuditAction,
    val fieldName: String? = null, // e.g., "amount"
    val oldValue: String? = null,
    val newValue: String? = null,
    val timestamp: LocalDateTime = LocalDateTime.now()
)
