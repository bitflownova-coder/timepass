package com.bitflow.finance.domain.model

import java.time.LocalDate
import java.time.LocalDateTime

enum class AccountType {
    BANK, CREDIT_CARD, WALLET, CASH
}

data class Account(
    val id: Long = 0,
    val name: String,
    val type: AccountType,
    val color: Int, // Color int
    val icon: String, // Icon name or resource id identifier
    val initialBalance: Double,
    val currentBalance: Double = initialBalance,
    val currency: String = "₹", // Account-specific currency
    val context: AppMode = AppMode.PERSONAL
)
