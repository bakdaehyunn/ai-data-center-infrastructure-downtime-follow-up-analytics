plugins {
    kotlin("jvm") version "2.0.21"
    application
}

group = "com.dcai.semantic"
version = "2026.06.phase14-read-only-graph-access"

description = "Read-only Fuseki/TDB2 graph access boundary for the ontology-native semantic service."

dependencies {
    // Jena 5.6.0 keeps this Phase 14 baseline compatible with the current JDK 17
    // verification image. Revisit the version when the service toolchain moves.
    implementation("org.apache.jena:jena-arq:5.6.0")
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

// Phase 14 intentionally does not apply a web framework plugin, define
// controllers, generate runtime DTOs, write graphs, or run reasoning. The graph
// boundary is read-only and limited to connectivity/query-health behavior.
