package com.bitflow.finance.data.local.entity

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "clients")
data class ClientEntity(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    val userId: String,
    val name: String,
    val email: String = "",
    val phone: String = "",
    val address: String = "",
    val gstin: String = "",
    val panNumber: String = "",
    val notes: String = "",
    val createdAt: Long = System.currentTimeMillis()
)
