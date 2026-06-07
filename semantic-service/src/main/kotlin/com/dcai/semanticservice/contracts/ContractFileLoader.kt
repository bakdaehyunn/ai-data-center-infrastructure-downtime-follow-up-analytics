package com.dcai.semanticservice.contracts

import java.nio.file.Files
import java.nio.file.Path

class ContractFileLoader {
    fun load(repoRoot: Path, artifact: ContractArtifact): LoadedContract {
        val resolved = repoRoot.resolve(artifact.path).normalize()
        return LoadedContract(
            artifact = artifact,
            absolutePath = resolved,
            content = if (Files.exists(resolved)) Files.readString(resolved) else null,
        )
    }
}

data class LoadedContract(
    val artifact: ContractArtifact,
    val absolutePath: Path,
    val content: String?,
) {
    val exists: Boolean = content != null
    val isNotBlank: Boolean = !content.isNullOrBlank()
}
