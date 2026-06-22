package com.reskiosk.ui

import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.rememberScrollState
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.BrokenImage
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.unit.dp
import coil.compose.SubcomposeAsyncImage
import com.reskiosk.network.ImageEvidence

/**
 * Phase 10 / Slice 7D — renders image evidence returned with an answer (RK-93/95/96/105).
 *
 * - Loads the hub-generated DISPLAY rendition via `renderRef` (not the original) over the
 *   local network — RK-105 (thumbnail/rendition-first).
 * - `ContentScale.Fit` preserves aspect ratio; no cropping — RK-93.
 * - Coil's loading/error slots give a spinner + a safe broken-image placeholder; a broken
 *   reference never crashes the kiosk and the text answer above it stays visible — RK-96.
 * - `imagePrimary` (RK-95 / D17): when true the top image leads ("Here is the image");
 *   when false the same images are shown but framed as tentative ("Possible matches"),
 *   never authoritative.
 *
 * DRAFT (unverified — needs Gradle sync for Coil + build/QA). Call this from the assistant
 * chat bubble, passing the configured hub base URL and `message.imageEvidence`.
 */
@Composable
fun ImageEvidenceSection(
    hubBaseUrl: String?,
    evidence: List<ImageEvidence>?,
    imagePrimary: Boolean,
    modifier: Modifier = Modifier,
) {
    if (evidence.isNullOrEmpty() || hubBaseUrl.isNullOrBlank()) return

    Column(modifier = modifier.fillMaxWidth().padding(top = 8.dp)) {
        Text(
            text = if (imagePrimary) "Here is the image:" else "Possible matches:",
            style = MaterialTheme.typography.labelLarge,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            modifier = Modifier.padding(bottom = 6.dp),
        )

        // Primary image (top hit) — larger, leads the display.
        EvidenceImage(
            url = buildAssetUrl(hubBaseUrl, evidence.first().renderRef),
            description = evidence.first().answerText ?: "image result",
            heightDp = if (imagePrimary) 220 else 160,
        )

        // Alternates — a small horizontally-scrollable strip (RK image top-N=3).
        val alternates = evidence.drop(1)
        if (alternates.isNotEmpty()) {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .horizontalScroll(rememberScrollState())
                    .padding(top = 6.dp),
                horizontalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                alternates.forEach { ev ->
                    EvidenceImage(
                        url = buildAssetUrl(hubBaseUrl, ev.renderRef),
                        description = ev.answerText ?: "image result",
                        heightDp = 96,
                        widthDp = 96,
                    )
                }
            }
        }
    }
}

@Composable
private fun EvidenceImage(
    url: String?,
    description: String,
    heightDp: Int,
    widthDp: Int? = null,
) {
    if (url == null) return
    val shape = RoundedCornerShape(12.dp)
    val sizeModifier = if (widthDp != null) {
        Modifier.size(width = widthDp.dp, height = heightDp.dp)
    } else {
        Modifier.fillMaxWidth().height(heightDp.dp)
    }
    Surface(
        modifier = sizeModifier.clip(shape),
        color = MaterialTheme.colorScheme.surfaceVariant,
        shape = shape,
    ) {
        SubcomposeAsyncImage(
            model = url,
            contentDescription = description,
            contentScale = ContentScale.Fit,   // preserve aspect ratio; no crop
            loading = {
                Box(Modifier.fillMaxWidth(), contentAlignment = Alignment.Center) {
                    CircularProgressIndicator(strokeWidth = 2.dp)
                }
            },
            error = {
                // Safe placeholder — broken/missing ref never breaks the answer (RK-96).
                Box(Modifier.fillMaxWidth(), contentAlignment = Alignment.Center) {
                    Icon(
                        imageVector = Icons.Filled.BrokenImage,
                        contentDescription = "image unavailable",
                        tint = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                }
            },
        )
    }
}

/** Join the configured hub base URL with a hub-relative render ref ("/assets/{id}/display"). */
fun buildAssetUrl(baseUrl: String?, renderRef: String?): String? {
    if (baseUrl.isNullOrBlank() || renderRef.isNullOrBlank()) return null
    return baseUrl.trimEnd('/') + renderRef
}
