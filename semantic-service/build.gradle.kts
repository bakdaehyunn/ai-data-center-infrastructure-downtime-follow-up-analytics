plugins {
    kotlin("jvm") version "2.0.21"
    application
}

group = "com.dcai.semantic"
version = "2026.06.post-phase20-private-query-endpoint"

description = "Private semantic query endpoint boundary for the ontology-native semantic service."

dependencies {
    // Jena 5.6.0 keeps this Phase 20 baseline compatible with the current JDK 17
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

// The post-Phase-20 private endpoint uses the JDK loopback HTTP server only
// when explicitly requested. It does not apply a web framework plugin, generate
// runtime DTOs, run reasoning, expose public endpoints, or allow graph writes.
