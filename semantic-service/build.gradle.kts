plugins {
    kotlin("jvm") version "2.0.21"
}

group = "com.dcai.semantic"
version = "2026.06.phase11-contract-validation"

description = "Contract-loading and static-validation slice for the future ontology-native semantic service."

dependencies {
    testImplementation(kotlin("test-junit5"))
}

kotlin {
    jvmToolchain(17)
}

tasks.test {
    useJUnitPlatform()
}

// Phase 11 intentionally does not apply a web/runtime plugin, declare
// application entry points, define controllers, generate DTOs, or connect to
// Fuseki/TDB2. The code is limited to local contract loading and static
// validation.
