package com.aptplayer.app

import androidx.media3.common.util.UnstableApi
import androidx.media3.exoplayer.ExoPlayer
import androidx.media3.session.MediaSession
import androidx.media3.session.MediaSessionService

/**
 * Mantém o áudio tocando fora do app.
 *
 * Sem um serviço em primeiro plano o Android corta a reprodução quando a tela
 * apaga. Ele também é o que faz aparecer a notificação com os controles e os
 * botões do fone funcionarem.
 */
@UnstableApi
class PlayerService : MediaSessionService() {

    private var session: MediaSession? = null

    override fun onCreate() {
        super.onCreate()
        val player = ExoPlayer.Builder(this).build()
        session = MediaSession.Builder(this, player).build()
    }

    override fun onGetSession(controllerInfo: MediaSession.ControllerInfo) = session

    override fun onDestroy() {
        session?.run {
            player.release()
            release()
        }
        session = null
        super.onDestroy()
    }
}
