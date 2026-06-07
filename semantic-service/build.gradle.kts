plugins {
    kotlin("jvm") version "2.0.21"
    application
}

group = "com.dcai.semantic"
version = "2026.06.phase17-query-result-contract-shaping"

description = "Query result contract shaping boundary for the ontology-native semantic service."

dependencies {
    // Jena 5.6.0 keeps this Phase 17 baseline compatible with the current JDK 17
    // verification image. Revisit the version when the service toolchain moves.
    implementation("org.apache.jena:jena-arq:5.6.0")
    implementation("org.apache.jena:jena-shacl:5.6.0")
    testImplementation(kotlin("test-junit5"))
}

kotlin {
    jvmToolchain(17)
}

tasks.test {
    useJUnitPlatform()
}

application {
    mainClass.set("com.dcai.semanticservice.runtime.SemanticServiceApplication")
}

// Phase 17 intentionally does not apply a web framework plugin, define
// controllers, generate runtime DTOs, run reasoning, or expose unrestricted graph
// writes. Query execution is CLI-only; result envelopes prepare future DTOs.
