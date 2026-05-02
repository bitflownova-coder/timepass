package com.bitflow.finance.data.local.entity

import androidx.room.Entity
import androidx.room.Index
import androidx.room.PrimaryKey

/**
 * Individual shares in a split expense
 * Tracks who owes how much for each expense
 */
@Entity(
    tableName = "split_expense_shares",
    indices = [
        Index(value = ["expenseId"]),
        Index(value = ["userId"])
    ]
)
data class SplitExpenseShareEntity(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val expenseId: String,
    val userId: String, // Who owes this amount
    val shareAmount: Double, // Amount this person owes
    val isPaid: Boolean = false, // Whether this person has settled their share
    val paidAt: Long? = null
)
