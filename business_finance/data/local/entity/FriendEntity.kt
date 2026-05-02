package com.bitflow.finance.data.local.entity

import androidx.room.Entity
import androidx.room.Index

/**
 * Friends/Contacts for bill splitting
 * Users add friends ONLY by UUID - NO username/nickname allowed
 * Display name comes from friend's UserAccountEntity.displayName
 */
@Entity(
    tableName = "friends",
    primaryKeys = ["userId", "friendUserId"],
    indices = [Index(value = ["userId", "friendUserId"], unique = true)]
)
data class FriendEntity(
    val userId: String, // Owner of this friend entry
    val friendUserId: String, // Friend's UUID (ONLY way to add friends)
    val addedAt: Long = System.currentTimeMillis()
)
