package com.aptplayer.app

import android.app.Application

/** Inicializa o extractor uma vez, ao abrir o app. */
class AptApp : Application() {
    override fun onCreate() {
        super.onCreate()
        YouTube.init()
    }
}
