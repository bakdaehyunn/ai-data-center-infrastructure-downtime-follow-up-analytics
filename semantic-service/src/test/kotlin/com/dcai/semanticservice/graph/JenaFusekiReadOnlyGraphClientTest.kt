package com.dcai.semanticservice.graph

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertTrue

class JenaFusekiReadOnlyGraphClientTest {
    @Test
    fun reportsUnreachableEndpointWithoutThrowing() {
        val client = JenaFusekiReadOnlyGraphClient(
            FusekiReadOnlyConfig(
                datasetUrl = "http://127.0.0.1:1/infrastructure",
                queryEndpointUrl = "http://127.0.0.1:1/infrastructure/query",
            ),
        )

        val check = client.checkConnectivity()

        assertFalse(check.reachable)
        assertEquals("http://127.0.0.1:1/infrastructure", check.datasetUrl)
        assertTrue(check.message.isNotBlank())
    }
}
