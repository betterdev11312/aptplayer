package com.aptplayer.app

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.view.inputmethod.EditorInfo
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

            override fun onMediaItemTransition(item: MediaItem?, reason: Int) {
                // quando a faixa acaba, segue para a próxima da lista
                val index = queue.indexOfFirst { it.videoId == current?.videoId }
                if (index >= 0 && index + 1 < queue.size) {
                    play(queue[index + 1])
                }
            }
        })

        ui.results.layoutManager = LinearLayoutManager(this)
        ui.results.adapter = adapter

        ui.searchInput.setOnEditorActionListener { view, actionId, _ ->
            if (actionId == EditorInfo.IME_ACTION_SEARCH) {
                search(view.text.toString())
                true
            } else {
                false
            }
        }

        ui.playPause.setOnClickListener {
            if (player.isPlaying) player.pause() else player.play()
        }
        ui.next.setOnClickListener { skip(1) }
        ui.previous.setOnClickListener { skip(-1) }
    }

    private fun search(query: String) {
        if (query.isBlank()) return

        ui.status.text = getString(R.string.searching)
        ui.status.isVisible = true

        lifecycleScope.launch {
            val found = withContext(Dispatchers.IO) {
                runCatching { YouTube.search(query, 25) }.getOrElse { emptyList() }
            }
            queue = found
            adapter.submit(found)
            ui.status.isVisible = found.isEmpty()
            if (found.isEmpty()) ui.status.text = getString(R.string.no_results)
        }
    }

    private fun play(track: YouTube.Track) {
        current = track
        ui.nowTitle.text = track.title
        ui.nowArtist.text = track.artist
        ui.nowArt.load(track.thumbnail)
        ui.playerBar.isVisible = true

        lifecycleScope.launch {
            val url = withContext(Dispatchers.IO) {
                runCatching { YouTube.audioUrl(track.videoId) }.getOrNull()
            }
            if (url == null) {
                ui.nowArtist.text = "não consegui tocar esta faixa"
                return@launch
            }
            player.setMediaItem(MediaItem.fromUri(url))
            player.prepare()
            player.play()
        }
    }

    private fun skip(delta: Int) {
        val index = queue.indexOfFirst { it.videoId == current?.videoId }
        val next = index + delta
        if (index >= 0 && next in queue.indices) play(queue[next])
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
