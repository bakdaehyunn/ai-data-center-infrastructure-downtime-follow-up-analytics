package com.dcai.semanticservice.contracts

data class ContractArtifact(
    val path: String,
    val requiredMarkers: Set<String>,
)
