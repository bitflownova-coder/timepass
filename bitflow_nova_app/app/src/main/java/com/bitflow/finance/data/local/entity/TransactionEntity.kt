package com.bitflow.finance.data.local.entity

import androidx.room.Entity
import androidx.room.Index
import androidx.room.PrimaryKey
import com.bitflow.finance.domain.model.TransactionDirection
import java.time.LocalDate
import java.time.LocalDateTime

@Entity(
    tableName = "transactions",
    indices = [
        Index(value = ["userId", "accountId", "txnDate"], name = "idx_user_account_date"),
        Index(value = ["userId", "txnDate"], name = "idx_user_date"),
        Index(value = ["accountId", "txnDate", "amount", "description"], name = "idx_dedup")
    ]
)
data class TransactionEntity(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val userId: String, // Owner of this transaction
    val accountId: Long,
    val txnDate: LocalDate,
    val valueDate: LocalDate?,
    val description: String,
    val reference: String?,
    val amount: Double,
    val direction: TransactionDirection,
    val categoryId: Long?,
    val merchantName: String? = null, // For auto-learning and subscription detection
    val tags: List<String>,
    val billPhotoUri: String?,
    val notes: String?,
    val balanceAfterTxn: Double? = null, // Balance from bank statement
    val isAutoCategorized: Boolean = false, // Track if category was predicted
    val context: com.bitflow.finance.domain.model.AppMode = com.bitflow.finance.domain.model.AppMode.PERSONAL, // PERSONAL or BUSINESS
    val linkedGoalId: Long? = null,
    val createdAt: LocalDateTime,
    val updatedAt: LocalDateTime
)
