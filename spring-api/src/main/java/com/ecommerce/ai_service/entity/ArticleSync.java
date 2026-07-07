package com.ecommerce.ai_service.entity;

import jakarta.persistence.*;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.Instant;

/**
 * Tracks the sync state of each OptiSigns support article.
 * Mirrors the SQLite schema used by the Python scraper so the Spring API
 * can query sync history without a separate DB.
 */
@Entity
@Table(name = "article_sync")
@Data
@NoArgsConstructor
public class ArticleSync {

    @Id
    @Column(name = "id", length = 64)
    private String id;               // Zendesk article ID (string)

    @Column(name = "slug")
    private String slug;

    @Column(name = "url", length = 512)
    private String url;

    @Column(name = "content_hash", length = 64)
    private String contentHash;

    @Column(name = "updated_at", length = 64)
    private String updatedAt;        // ISO-8601 from Zendesk

    @Column(name = "openai_file_id", length = 128)
    private String openaiFileId;

    @Column(name = "synced_at", length = 64)
    private String syncedAt;         // ISO-8601 of last successful upload
}
