pluginManagement {
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}

dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
        // NewPipeExtractor e publicado aqui, nao no Maven Central
        maven { url = uri("https://jitpack.io") }
    }
}

rootProject.name = "AptPlayer"
include(":app")
