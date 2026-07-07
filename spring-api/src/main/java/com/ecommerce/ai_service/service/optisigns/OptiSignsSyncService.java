package com.ecommerce.ai_service.service.optisigns;

import com.ecommerce.ai_service.entity.ArticleSync;
import com.ecommerce.ai_service.repository.ArticleSyncRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Spring-side sync status service.
 *
 * <p>The actual heavy-lifting (scrape → convert → upload) is done by the
 * Python pipeline (scraper/main.py).  This service provides:
 *  <ul>
 *    <li>A REST endpoint to manually trigger the Python pipeline via Process.</li>
 *    <li>A view of the last sync stats from the shared article_sync table.</li>
 *    <li>A @Scheduled daily job that kicks off the Python pipeline at 02:00 UTC.</li>
 *  </ul>
 *
 * <p>The Python process and the Spring app share the same SQLite DB mounted at
 * the path configured in DELTA_DB_PATH.  In Docker Compose, they share the
 * same named volume.
 */
@Service
@RequiredArgsConstructor
@Slf4j
public class OptiSignsSyncService {

    private final ArticleSyncRepository syncRepo;

    /**
     * Returns current sync statistics from the shared DB.
     */
    public Map<String, Object> getSyncStatus() {
        List<ArticleSync> all = syncRepo.findAll();

        Map<String, Object> stats = new HashMap<>();
        stats.put("totalArticles",   all.size());
        stats.put("uploadedToOpenAI", syncRepo.countByOpenaiFileIdIsNotNull());
        stats.put("lastSyncedAt",
                all.stream()
                   .map(ArticleSync::getSyncedAt)
                   .max(String::compareTo)
                   .orElse("never"));
        return stats;
    }

    /**
     * Runs daily at 02:00 UTC.
     * Triggers the Python pipeline as a child process.
     */
    @Scheduled(cron = "0 0 2 * * *")
    public void scheduledSync() {
        log.info("[OptiSync] Scheduled daily sync triggered.");
        runPipeline(false);
    }

    /**
     * Manually trigger the Python pipeline (called from REST controller).
     *
     * @param testMode if true, passes --test flag to run a sample question after sync
     */
    public Map<String, Object> triggerSync(boolean testMode) {
        log.info("[OptiSync] Manual sync triggered. testMode={}", testMode);
        int exitCode = runPipeline(testMode);
        Map<String, Object> result = new HashMap<>();
        result.put("exitCode", exitCode);
        result.put("success",  exitCode == 0);
        result.put("stats",    getSyncStatus());
        return result;
    }

    // ── Private helpers ───────────────────────────────────────────────────────

    private int runPipeline(boolean testMode) {
        try {
            String pythonCmd = System.getenv().getOrDefault("PYTHON_CMD", "python");
            String scriptPath = System.getenv().getOrDefault(
                    "SCRAPER_SCRIPT", "/app/scraper/main.py");

            ProcessBuilder pb = new ProcessBuilder(
                    pythonCmd, scriptPath,
                    testMode ? "--test" : ""
            );
            pb.redirectErrorStream(true);
            pb.inheritIO();

            Process process = pb.start();
            int exitCode = process.waitFor();
            log.info("[OptiSync] Pipeline finished with exit code {}", exitCode);
            return exitCode;
        } catch (Exception e) {
            log.error("[OptiSync] Failed to run pipeline: {}", e.getMessage(), e);
            return -1;
        }
    }
}
