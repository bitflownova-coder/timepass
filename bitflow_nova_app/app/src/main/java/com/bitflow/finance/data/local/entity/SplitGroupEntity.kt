package com.bitflow.finance.data.local.entity

import androidx.room.Entity
import androidx.room.Index
import androidx.room.PrimaryKey

/**
 * Split groups for bill splitting
 * Can have 2 or more members
 */
@Entity(
    tableName = "split_groups",
    indices = [Index(value = ["createdBy"])]
)
data class SplitGroupEntity(
    @PrimaryKey val groupId: String, // UUID for group
    val groupName: String,
    val description: String? = null,
    val createdBy: String, // userId of creator
    val createdAt: Long = System.currentTimeMillis(),
    val isActive: Boolean = true
)
