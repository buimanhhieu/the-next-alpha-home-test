package com.ecommerce.ai_service.repository;

import com.ecommerce.ai_service.entity.ArticleSync;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;

@Repository
public interface ArticleSyncRepository extends JpaRepository<ArticleSync, String> {
    Optional<ArticleSync> findByUrl(String url);
    long countByOpenaiFileIdIsNotNull();
}
