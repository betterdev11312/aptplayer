package com.aptplayer.app

import android.os.Bundle
import android.util.Log
import android.view.LayoutInflater
import android.view.ViewGroup
import android.view.inputmethod.EditorInfo
import android.view.inputmethod.InputMethodManager
import androidx.appcompat.app.AppCompatActivity
import androidx.core.view.isVisible
import androidx.lifecycle.lifecycleScope
import androidx.media3.common.MediaItem
import androidx.media3.common.Player
import androidx.media3.common.util.UnstableApi
import androidx.media3.exoplayer.ExoPlayer
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import coil.load
import com.aptplayer.app.databinding.ActivityMainBinding
import com.aptplayer.app.databinding.ItemTrackBinding
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

private const val TAG = "AptPlayer"

@UnstableApi
class MainActivity : AppCompatActivity() {

    private lateinit var ui: ActivityMainBinding
    private lateinit var player: ExoPlayer
    private val adapter = TrackAdapter { track -> play(track) }
    private var queue: List<YouTube.Track> = emptyList()
    private var current: YouTube.Track? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        ui = ActivityMainBinding.inflate(layoutInflater)
        setContentView(ui.root)

        player = ExoPlayer.Builder(this).build()
        player.addListener(object : Player.Listener {
            override fun onIsPlayingChanged(isPlaying: Boolean) {
                ui.playPause.setImageResource(
                    if (isPlaying) android.R.drawable.ic_media_pause
                    else android.R.drawable.ic_media_play,
                )
            }

            override fun onPlaybackStateChanged(state: Int) {
                if (state == Player.STATE_ENDED) skip(1)
            }

            override fun onPlayerError(error: androidx.media3.common.PlaybackException) {
                Log.e(TAG, "erro de reproducao", error)
                ui.nowArtist.text = "erro ao tocar — tente outra faixa"
            }
        })

        ui.results.layoutManager = LinearLayoutManager(this)
        ui.results.adapter = adapter

        ui.searchInput.setOnEditorActionListener { view, actionId, _ ->
            if (actionId == EditorInfo.IME_ACTION_SEARCH) {
                esconderTeclado()
                search(view.text.toString())
                true
            } else {
                false
            }
        }
        ui.searchButton.setOnClickListener {
            esconderTeclado()
            search(ui.searchInput.text.toString())
        }

        ui.playPause.setOnClickListener {
            if (player.isPlaying) player.pause() else player.play()
        }
        ui.next.setOnClickListener { skip(1) }
        ui.previous.setOnClickListener { skip(-1) }

        mostrarEstado("busque uma música para começar", carregando = false)
    }

    private fun esconderTeclado() {
        val imm = getSystemService(INPUT_METHOD_SERVICE) as InputMethodManager
        imm.hideSoftInputFromWindow(ui.searchInput.windowToken, 0)
    }

    private fun mostrarEstado(texto: String, carregando: Boolean) {
        ui.status.text = texto
        ui.status.isVisible = true
        ui.progress.isVisible = carregando
        ui.results.isVisible = false
    }

    private fun mostrarResultados(lista: List<YouTube.Track>) {
        adapter.submit(lista)
        ui.status.isVisible = false
        ui.progress.isVisible = false
        ui.results.isVisible = true
    }

    private fun search(query: String) {
        if (query.isBlank()) return
        mostrarEstado("buscando \"$query\"...", carregando = true)

        lifecycleScope.launch {
            // O erro precisa chegar até aqui: engolir a exceção deixava a tela
            // vazia sem explicação nenhuma.
            val resultado = withContext(Dispatchers.IO) {
                try {
                    Result.success(YouTube.search(query, 25))
                } catch (exc: Exception) {
                    Log.e(TAG, "falha na busca", exc)
                    Result.failure(exc)
                }
            }

            resultado.fold(
                onSuccess = { lista ->
                    queue = lista
                    if (lista.isEmpty()) {
                        mostrarEstado(
                            "nenhuma música encontrada para \"$query\"",
                            carregando = false,
                        )
                    } else {
                        mostrarResultados(lista)
                    }
                },
                onFailure = { erro ->
                    mostrarEstado(
                        "não consegui buscar.\n${erro.javaClass.simpleName}: " +
                            (erro.message ?: "sem detalhes"),
                        carregando = false,
                    )
                },
            )
        }
    }

    private fun play(track: YouTube.Track) {
        current = track
        ui.nowTitle.text = track.title
        ui.nowArtist.text = "carregando..."
        ui.nowArt.load(track.thumbnail)
        ui.playerBar.isVisible = true

        lifecycleScope.launch {
            val url = withContext(Dispatchers.IO) {
                try {
                    YouTube.audioUrl(track.videoId)
                } catch (exc: Exception) {
                    Log.e(TAG, "falha ao resolver audio", exc)
                    null
                }
            }

            if (url == null) {
                ui.nowArtist.text = "não consegui tocar esta faixa"
                return@launch
            }

            ui.nowArtist.text = track.artist
            player.setMediaItem(MediaItem.fromUri(url))
            player.prepare()
            player.play()
        }
    }

    private fun skip(delta: Int) {
        val index = queue.indexOfFirst { it.videoId == current?.videoId }
        val proximo = index + delta
        if (index >= 0 && proximo in queue.indices) play(queue[proximo])
    }

    override fun onDestroy() {
        player.release()
        super.onDestroy()
    }
}

/** Lista de faixas. */
private class TrackAdapter(
    private val onClick: (YouTube.Track) -> Unit,
) : RecyclerView.Adapter<TrackAdapter.Holder>() {

    private var items: List<YouTube.Track> = emptyList()

    fun submit(list: List<YouTube.Track>) {
        items = list
        notifyDataSetChanged()
    }

    class Holder(val ui: ItemTrackBinding) : RecyclerView.ViewHolder(ui.root)

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): Holder {
        val binding = ItemTrackBinding.inflate(
            LayoutInflater.from(parent.context), parent, false,
        )
        return Holder(binding)
    }

    override fun onBindViewHolder(holder: Holder, position: Int) {
        val track = items[position]
        holder.ui.title.text = track.title
        holder.ui.artist.text = track.artist
        holder.ui.duration.text = track.durationLabel
        holder.ui.art.load(track.thumbnail)
        holder.itemView.setOnClickListener { onClick(track) }
    }

    override fun getItemCount() = items.size
}
