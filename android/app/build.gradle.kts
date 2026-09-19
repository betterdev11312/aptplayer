plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "com.aptplayer.app"
    compileSdk = 35

    defaultConfig {
        applicationId = "com.aptplayer.app"
        minSdk = 24              // Android 7.0 — cobre praticamente todo mundo
        targetSdk = 35
        versionCode = 1
        versionName = "1.0.0"
    }

    buildTypes {
        release {
            // O APK sai fora da Play Store, entao assinamos com a chave de
            // debug para nao exigir keystore na primeira build.
            isMinifyEnabled = true
            isShrinkResources = true
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro",
            )
            signingConfig = signingConfigs.getByName("debug")
        }
    }

    compileOptions {
        // NewPipeExtractor usa recursos modernos de Java; o desugaring
        // permite isso mesmo nos Androids mais antigos que suportamos.
        isCoreLibraryDesugaringEnabled = true
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = "17"
    }

    buildFeatures {
        viewBinding = true
    }

    packaging {
        resources.excludes += setOf(
            "META-INF/DEPENDENCIES",
            "META-INF/LICENSE*",
            "META-INF/NOTICE*",
        )
    }
}

dependencies {
    // Resolve o audio do YouTube sem Python - e o que o NewPipe usa.
    implementation("com.github.TeamNewPipe:NewPipeExtractor:v0.26.5")

    // Reproducao de audio, incluindo streams HTTP progressivos.
    implementation("androidx.media3:media3-exoplayer:1.5.0")
    implementation("androidx.media3:media3-session:1.5.0")
    implementation("androidx.media3:media3-ui:1.5.0")

    // Interface
    implementation("androidx.core:core-ktx:1.15.0")
    implementation("androidx.appcompat:appcompat:1.7.0")
    implementation("com.google.android.material:material:1.12.0")
    implementation("androidx.constraintlayout:constraintlayout:2.2.0")
    implementation("androidx.recyclerview:recyclerview:1.3.2")
    implementation("androidx.lifecycle:lifecycle-runtime-ktx:2.8.7")
    implementation("androidx.lifecycle:lifecycle-viewmodel-ktx:2.8.7")

    // Banco local: mesma ideia do SQLite do desktop
    implementation("androidx.room:room-runtime:2.6.1")
    implementation("androidx.room:room-ktx:2.6.1")
    annotationProcessor("androidx.room:room-compiler:2.6.1")

    // Capas
    implementation("io.coil-kt:coil:2.7.0")

    coreLibraryDesugaring("com.android.tools:desugar_jdk_libs:2.1.3")
}
