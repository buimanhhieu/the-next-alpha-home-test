package com.ecommerce.ai_service.controller;

import com.ecommerce.ai_service.service.optisigns.OptiSignsSyncService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

/**
 * REST endpoints for the OptiSigns sync pipeline.
 *
 * <pre>
 * GET  /api/optisigns/status   → sync statistics
 * POST /api/optisigns/sync     → manually trigger scrape + upload
 * POST /api/optisigns/sync?test=true → trigger + run test question
 * </pre>
 */
@RestController
@RequestMapping("/api/optisigns")
@RequiredArgsConstructor
public class OptiSignsSyncController {

    private final OptiSignsSyncService syncService;

    /** Return current sync status from the shared SQLite/Postgres DB. */
    @GetMapping("/status")
    public ResponseEntity<Map<String, Object>> status() {
        return ResponseEntity.ok(syncService.getSyncStatus());
    }

    /** Manually trigger the Python pipeline. */
    @PostMapping("/sync")
    public ResponseEntity<Map<String, Object>> triggerSync(
            @RequestParam(value = "test", defaultValue = "false") boolean test) {
        Map<String, Object> result = syncService.triggerSync(test);
        int exitCode = (int) result.getOrDefault("exitCode", -1);
        return exitCode == 0
                ? ResponseEntity.ok(result)
                : ResponseEntity.internalServerError().body(result);
    }
}
