package com.bitflow.finance.data.repository

import com.bitflow.finance.data.local.dao.FriendDao
import com.bitflow.finance.data.local.dao.UserAccountDao
import com.bitflow.finance.data.local.entity.FriendEntity
import com.bitflow.finance.data.local.entity.UserAccountEntity
import com.bitflow.finance.domain.repository.FriendRepository
import com.bitflow.finance.domain.repository.FriendWithUser
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class FriendRepositoryImpl @Inject constructor(
    private val friendDao: FriendDao,
    private val userAccountDao: UserAccountDao
) : FriendRepository {
    
    override fun getFriends(userId: String): Flow<List<FriendEntity>> {
        return friendDao.getFriendsByUser(userId)
    }
    
    override fun getFriendsWithUserInfo(userId: String): Flow<List<FriendWithUser>> {
        return friendDao.getFriendsByUser(userId).map { friends ->
            friends.map { friend ->
                FriendWithUser(
                    friendEntity = friend,
                    userAccount = userAccountDao.getUserById(friend.friendUserId)
                )
            }
        }
    }
    
    override suspend fun addFriend(
        userId: String, 
        friendUserId: String
    ): Result<Unit> {
        return try {
            if (userId == friendUserId) {
                return Result.failure(Exception("Cannot add yourself as a friend"))
            }
            
            // Validate that the friend UUID exists
            val friendUser = userAccountDao.getUserById(friendUserId)
            if (friendUser == null || !friendUser.isActive) {
                return Result.failure(Exception("Invalid UUID - user not found"))
            }
            
            val existingFriend = friendDao.getFriend(userId, friendUserId)
            if (existingFriend != null) {
                return Result.failure(Exception("Friend already added"))
            }
            
            val friend = FriendEntity(
                userId = userId,
                friendUserId = friendUserId,
                addedAt = System.currentTimeMillis()
            )
            friendDao.insertFriend(friend)
            Result.success(Unit)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    override suspend fun removeFriend(userId: String, friendUserId: String): Result<Unit> {
        return try {
            friendDao.deleteFriend(userId, friendUserId)
            Result.success(Unit)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    override suspend fun isFriend(userId: String, friendUserId: String): Boolean {
        return friendDao.getFriend(userId, friendUserId) != null
    }
    
    override suspend fun validateFriendUuid(friendUserId: String): Result<UserAccountEntity> {
        return try {
            val user = userAccountDao.getUserById(friendUserId)
            if (user != null && user.isActive) {
                Result.success(user)
            } else {
                Result.failure(Exception("Invalid UUID - user not found"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
}
