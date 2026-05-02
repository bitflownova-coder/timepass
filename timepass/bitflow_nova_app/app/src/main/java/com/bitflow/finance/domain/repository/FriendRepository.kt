package com.bitflow.finance.domain.repository

import com.bitflow.finance.data.local.entity.FriendEntity
import com.bitflow.finance.data.local.entity.UserAccountEntity
import kotlinx.coroutines.flow.Flow

data class FriendWithUser(
    val friendEntity: FriendEntity,
    val userAccount: UserAccountEntity?
)

interface FriendRepository {
    fun getFriends(userId: String): Flow<List<FriendEntity>>
    
    fun getFriendsWithUserInfo(userId: String): Flow<List<FriendWithUser>>
    
    suspend fun addFriend(userId: String, friendUserId: String): Result<Unit>
    
    suspend fun removeFriend(userId: String, friendUserId: String): Result<Unit>
    
    suspend fun isFriend(userId: String, friendUserId: String): Boolean
    
    suspend fun validateFriendUuid(friendUserId: String): Result<UserAccountEntity>
}
