plugins {
    kotlin("jvm") version "2.0.21"
    application
}

group = "com.dcai.semantic"
version = "2026.06.phase13-runnable-baseline"

description = "Runnable contract-validation baseline for the future ontology-native semantic service."

dependencies {
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

// Phase 13 intentionally does not apply a web framework plugin, define
// controllers, generate runtime DTOs, or connect to Fuseki/TDB2. The executable
// baseline only runs local contract validation and prints runtime readiness.
