package com.bitflow.finance.data.local.entity

import androidx.room.Entity
import androidx.room.PrimaryKey
import com.bitflow.finance.domain.model.ActivityType
import com.bitflow.finance.domain.model.AppMode

@Entity(tableName = "transaction_templates")
data class TransactionTemplateEntity(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    val userId: String,
    val name: String,
    val amount: Double,
    val type: ActivityType,
    val categoryId: Long,
    val description: String = "",
    val context: AppMode = AppMode.PERSONAL,
    val icon: String = "💳",
    val createdAt: Long = System.currentTimeMillis()
)
