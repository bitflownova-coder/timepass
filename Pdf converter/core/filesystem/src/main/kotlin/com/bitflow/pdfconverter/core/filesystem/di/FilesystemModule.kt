package com.bitflow.pdfconverter.core.filesystem.di

import com.bitflow.pdfconverter.core.filesystem.FileManager
import com.bitflow.pdfconverter.core.filesystem.SafHelper
import dagger.Module
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent

@Module
@InstallIn(SingletonComponent::class)
object FilesystemModule
// FileManager and SafHelper use @Inject constructors — Hilt provides them automatically.
// This module exists as an explicit extension point for future filesystem bindings.
