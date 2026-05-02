pluginManagement {
    repositories {
        google {
            content {
                includeGroupByRegex("com\\.android.*")
                includeGroupByRegex("com\\.google.*")
                includeGroupByRegex("androidx.*")
            }
        }
        mavenCentral()
        gradlePluginPortal()
    }
}

dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
        maven { url = uri("https://jitpack.io") }
    }
}

rootProject.name = "PdfConverter"

// App
include(":app")

// Core modules
include(":core:common")
include(":core:ui")
include(":core:data")
include(":core:domain")
include(":core:filesystem")

// Feature modules
include(":feature:scanner")
include(":feature:converter")
include(":feature:editor")
include(":feature:optimization")
include(":feature:security")
include(":feature:smarttools")
include(":feature:storage")
include(":feature:utility")
