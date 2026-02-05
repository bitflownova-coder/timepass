package com.bitflow.finance.data.local.entity

import androidx.room.Entity
import androidx.room.Index
import androidx.room.PrimaryKey

/**
 * Individual split expenses within a group
 */
@Entity(
    tableName = "split_expenses",
    indices = [
        Index(value = ["groupId"]),
        Index(value = ["paidBy"]),
        Index(value = ["expenseDate"])
    ]
)
data class SplitExpenseEntity(
    @PrimaryKey val expenseId: String, // UUID
    val groupId: String,
    val description: String,
    val totalAmount: Double,
    val paidBy: String, // userId who paid
    val expenseDate: Long,  // Timestamp
    val category: String? = null,
    val notes: String? = null,
    val createdAt: Long = System.currentTimeMillis(),
    val isSettled: Boolean = false
)
