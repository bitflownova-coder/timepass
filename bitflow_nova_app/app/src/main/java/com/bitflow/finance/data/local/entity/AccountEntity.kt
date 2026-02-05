package com.bitflow.finance.data.local.entity

import androidx.room.Entity
import androidx.room.PrimaryKey
import com.bitflow.finance.domain.model.AccountType

import com.bitflow.finance.domain.model.AppMode

@Entity(tableName = "accounts")
data class AccountEntity(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val userId: String, // Owner of this account
    val name: String,
    val type: AccountType,
    val color: Int,
    val icon: String,
    val initialBalance: Double,
    val currentBalance: Double,
    val currency: String = "₹",
    val context: AppMode = AppMode.PERSONAL // PERSONAL or BUSINESS
)
