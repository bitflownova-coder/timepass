package com.bitflow.finance.di

import com.bitflow.finance.data.repository.FriendRepositoryImpl
import com.bitflow.finance.data.repository.SplitRepositoryImpl
import com.bitflow.finance.domain.repository.FriendRepository
import com.bitflow.finance.domain.repository.SplitRepository
import dagger.Binds
import dagger.Module
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
abstract class SplitModule {
    
    @Binds
    @Singleton
    abstract fun bindFriendRepository(
        friendRepositoryImpl: FriendRepositoryImpl
    ): FriendRepository
    
    @Binds
    @Singleton
    abstract fun bindSplitRepository(
        splitRepositoryImpl: SplitRepositoryImpl
    ): SplitRepository
}
