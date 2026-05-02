package com.bitflow.finance.data.local.entity

import androidx.room.Entity
import androidx.room.PrimaryKey

enum class DebtStrategy {
    SNOWBALL, // Lowest balance first
    AVALANCHE // Highest interest first
}

@Entity(tableName = "debts")
data class DebtEntity(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val userId: String,
    val name: String,
    val currentBalance: Double,
    val interestRate: Double, // Annual percentage, e.g., 18.0
    val minimumPayment: Double,
    val dueDay: Int, // 1-31
    val strategy: DebtStrategy = DebtStrategy.AVALANCHE,
    val createdAt: Long = System.currentTimeMillis()
)
