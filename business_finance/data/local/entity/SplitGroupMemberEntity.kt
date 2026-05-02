package com.bitflow.finance.data.local.entity

import androidx.room.Entity
import androidx.room.Index
import androidx.room.PrimaryKey

/**
 * Members of a split group
 */
@Entity(
    tableName = "split_group_members",
    indices = [
        Index(value = ["groupId", "userId"], unique = true),
        Index(value = ["userId"])
    ]
)
data class SplitGroupMemberEntity(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val groupId: String,
    val userId: String, // Can be friend's UUID or own UUID
    val addedAt: Long = System.currentTimeMillis(),
    val isActive: Boolean = true
)
