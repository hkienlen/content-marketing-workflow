<?php

declare(strict_types=1);

if (!defined('ABSPATH')) {
    exit;
}

final class SEO_Workflow_Bridge_Publication_Controller
{
    private const OPTION = 'seo_workflow_bridge_settings';
    private const REQUEST_TTL = 86400;

    private const MANAGED_POST_META = '_seo_workflow_bridge_managed';
    private const MANIFEST_PATH_META = '_seo_workflow_bridge_manifest_path';
    private const SOURCE_COMMIT_META = '_seo_workflow_bridge_source_commit';
    private const SOURCE_ARTICLE_PATH_META = '_seo_workflow_bridge_source_article_path';
    private const SOURCE_ARTICLE_SHA_META = '_seo_workflow_bridge_source_article_sha256';

    private SEO_Workflow_Bridge_OIDC_Verifier $verifier;

    public function __construct(SEO_Workflow_Bridge_OIDC_Verifier $verifier)
    {
        $this->verifier = $verifier;
    }

    public function register(): void
    {
        add_action('rest_api_init', function (): void {
            register_rest_route('seo-workflow-bridge/v1', '/publish', [
                'methods' => 'POST',
                'callback' => [$this, 'execute'],
                'permission_callback' => '__return_true',
            ]);
        });
    }

    public function execute(WP_REST_Request $request): WP_REST_Response
    {
        $settings = $this->settings();
        if (empty($settings['enabled'])) {
            return $this->error('bridge_disabled', 'SEO Workflow Bridge is disabled.', 503);
        }

        $authorization = (string)$request->get_header('authorization');
        if (!preg_match('/^Bearer\s+(.+)$/i', $authorization, $matches)) {
            return $this->error('missing_bearer_token', 'A GitHub Actions OIDC bearer token is required.', 401);
        }

        $claims = $this->verifier->verify(trim($matches[1]), $settings);
        if (is_wp_error($claims)) {
            return $this->error($claims->get_error_code(), $claims->get_error_message(), 401);
        }

        $body = $request->get_json_params();
        if (!is_array($body)) {
            return $this->error('invalid_request', 'Request body must be a JSON object.', 400);
        }
        $validated = $this->validate_envelope($body);
        if (is_wp_error($validated)) {
            return $this->error($validated->get_error_code(), $validated->get_error_message(), 400);
        }

        $request_id = (string)$body['request_id'];
        if ($this->request_seen($request_id)) {
            return $this->error('replayed_request', 'This relay request_id has already been processed.', 409);
        }

        $operation = (string)$body['operation'];
        $payload = is_array($body['payload'] ?? null) ? $body['payload'] : [];
        $result = $this->dispatch($operation, $payload, $settings);
        if (is_wp_error($result)) {
            return $this->error($result->get_error_code(), $result->get_error_message(), 400, $request_id);
        }

        $this->mark_request_seen($request_id);
        return new WP_REST_Response([
            'ok' => true,
            'schema_version' => 1,
            'request_id' => $request_id,
            'operation' => $operation,
            'site_url' => site_url(),
            'result' => $result,
            'oidc' => [
                'repository_id' => (string)($claims['repository_id'] ?? ''),
                'run_id' => (string)($claims['run_id'] ?? ''),
                'workflow_ref' => (string)($claims['job_workflow_ref'] ?? ($claims['workflow_ref'] ?? '')),
            ],
        ], 200);
    }

    private function dispatch(string $operation, array $payload, array $settings)
    {
        if ($operation === 'publication_preflight') {
            if (empty($settings['allow_content_read'])) {
                return new WP_Error('content_read_disabled', 'Content read is disabled in the bridge settings.');
            }
            return $this->verify_candidate($payload, $settings, 'draft');
        }
        if ($operation === 'article_publish') {
            if (empty($settings['allow_article_publish'])) {
                return new WP_Error('article_publish_disabled', 'Article publication is disabled in the bridge settings.');
            }
            return $this->article_publish($payload, $settings);
        }
        if ($operation === 'published_article_read') {
            if (empty($settings['allow_content_read'])) {
                return new WP_Error('content_read_disabled', 'Content read is disabled in the bridge settings.');
            }
            return $this->verify_candidate($payload, $settings, 'publish');
        }
        return new WP_Error('unsupported_operation', 'Unsupported publication operation.');
    }

    private function article_publish(array $payload, array $settings)
    {
        $preflight = $this->verify_candidate($payload, $settings, 'draft');
        if (is_wp_error($preflight)) {
            return $preflight;
        }
        $post_id = (int)$preflight['id'];
        $updated = wp_update_post(['ID' => $post_id, 'post_status' => 'publish'], true);
        if (is_wp_error($updated)) {
            return $updated;
        }
        if ((int)$updated !== $post_id) {
            return new WP_Error('publish_id_mismatch', 'WordPress returned an unexpected post ID while publishing.');
        }
        $verified = $this->verify_candidate($payload, $settings, 'publish');
        if (is_wp_error($verified)) {
            return new WP_Error('publish_verification_failed', 'The article status changed to publish but post-publication verification failed: ' . $verified->get_error_message());
        }
        $verified['published_at_gmt'] = (string)get_post_field('post_date_gmt', $post_id);
        $verified['public_url'] = (string)get_permalink($post_id);
        return $verified;
    }

    private function verify_candidate(array $payload, array $settings, string $required_status)
    {
        $post_id = (int)($payload['post_id'] ?? 0);
        $expected = $payload['expected'] ?? null;
        if ($post_id <= 0 || !is_array($expected)) {
            return new WP_Error('invalid_publication_candidate', 'A positive post_id and expected snapshot are required.');
        }
        $post = get_post($post_id);
        if (!$post instanceof WP_Post) {
            return new WP_Error('publication_post_not_found', 'The publication candidate post was not found.');
        }
        if (get_post_meta($post_id, self::MANAGED_POST_META, true) !== '1') {
            return new WP_Error('publication_post_unmanaged', 'Only bridge-managed articles may be published by this operation.');
        }
        if ((string)$post->post_status !== $required_status) {
            return new WP_Error('publication_status_mismatch', 'Publication candidate status no longer matches the required state.');
        }

        $post_type = (string)($expected['post_type'] ?? '');
        $slug = sanitize_title((string)($expected['slug'] ?? ''));
        $title = (string)($expected['title'] ?? '');
        $excerpt = (string)($expected['excerpt'] ?? '');
        $content_sha = strtolower((string)($expected['content_sha256'] ?? ''));
        $featured_media_id = (int)($expected['featured_media_id'] ?? 0);
        $manifest_path = $this->repository_path((string)($expected['manifest_path'] ?? ''));
        $source_commit = strtolower((string)($expected['source_commit'] ?? ''));
        $source_article_path = $this->repository_path((string)($expected['source_article_path'] ?? ''));
        $source_article_sha = strtolower((string)($expected['source_article_sha256'] ?? ''));

        if (!in_array($post_type, ['post', 'page'], true) || $slug === '' || $title === '') {
            return new WP_Error('invalid_publication_identity', 'Expected post type, slug and title are required.');
        }
        if (!preg_match('/^[a-f0-9]{64}$/', $content_sha) || !preg_match('/^[a-f0-9]{40}$/', $source_commit) || !preg_match('/^[a-f0-9]{64}$/', $source_article_sha)) {
            return new WP_Error('invalid_publication_hashes', 'Expected content/source hashes are invalid.');
        }
        if ($manifest_path === '' || $source_article_path === '') {
            return new WP_Error('invalid_publication_source', 'Expected manifest and source article paths are required.');
        }

        $checks = [
            'post_type' => (string)$post->post_type === $post_type,
            'slug' => (string)$post->post_name === $slug,
            'title' => (string)$post->post_title === $title,
            'excerpt' => (string)$post->post_excerpt === $excerpt,
            'content_sha256' => hash_equals($content_sha, hash('sha256', (string)$post->post_content)),
            'featured_media_id' => (int)get_post_thumbnail_id($post_id) === $featured_media_id,
            'manifest_path' => (string)get_post_meta($post_id, self::MANIFEST_PATH_META, true) === $manifest_path,
            'source_commit' => (string)get_post_meta($post_id, self::SOURCE_COMMIT_META, true) === $source_commit,
            'source_article_path' => (string)get_post_meta($post_id, self::SOURCE_ARTICLE_PATH_META, true) === $source_article_path,
            'source_article_sha256' => (string)get_post_meta($post_id, self::SOURCE_ARTICLE_SHA_META, true) === $source_article_sha,
        ];

        $meta_checks = $this->verify_expected_meta($post_id, $expected['post_meta'] ?? [], $settings);
        if (is_wp_error($meta_checks)) {
            return $meta_checks;
        }
        foreach ($meta_checks as $key => $value) {
            $checks['post_meta:' . $key] = $value;
        }
        $taxonomy_checks = $this->verify_expected_taxonomies($post_id, $expected['taxonomies'] ?? [], $settings);
        if (is_wp_error($taxonomy_checks)) {
            return $taxonomy_checks;
        }
        foreach ($taxonomy_checks as $taxonomy => $value) {
            $checks['taxonomy:' . $taxonomy] = $value;
        }
        foreach ($checks as $name => $ok) {
            if (!$ok) {
                return new WP_Error('publication_candidate_drift', 'Publication candidate changed after validation: ' . $name);
            }
        }

        return [
            'id' => $post_id,
            'status' => (string)$post->post_status,
            'slug' => (string)$post->post_name,
            'title' => (string)$post->post_title,
            'content_sha256' => hash('sha256', (string)$post->post_content),
            'featured_media_id' => (int)get_post_thumbnail_id($post_id),
            'source_commit' => (string)get_post_meta($post_id, self::SOURCE_COMMIT_META, true),
            'source_article_path' => (string)get_post_meta($post_id, self::SOURCE_ARTICLE_PATH_META, true),
            'checks' => $checks,
            'public_url' => (string)get_permalink($post_id),
        ];
    }

    private function verify_expected_meta(int $post_id, $expected_meta, array $settings)
    {
        if ($expected_meta === null) {
            return [];
        }
        if (!is_array($expected_meta)) {
            return new WP_Error('invalid_publication_meta', 'expected.post_meta must be an object.');
        }
        $allowed = array_fill_keys($this->csv_list((string)($settings['allowed_prepare_meta_keys'] ?? '')), true);
        $checks = [];
        foreach ($expected_meta as $key => $expected_value) {
            if (!is_string($key) || !isset($allowed[$key])) {
                return new WP_Error('publication_meta_not_allowed', 'Publication candidate requested a meta key outside the configured allowlist.');
            }
            if (is_array($expected_value) || is_object($expected_value) || is_resource($expected_value)) {
                return new WP_Error('invalid_publication_meta_value', 'Publication candidate meta values must be scalar.');
            }
            $checks[$key] = (string)get_post_meta($post_id, $key, true) === (string)$expected_value;
        }
        return $checks;
    }

    private function verify_expected_taxonomies(int $post_id, $expected_taxonomies, array $settings)
    {
        if ($expected_taxonomies === null) {
            return [];
        }
        if (!is_array($expected_taxonomies)) {
            return new WP_Error('invalid_publication_taxonomies', 'expected.taxonomies must be an object.');
        }
        $allowed = array_fill_keys($this->csv_list((string)($settings['allowed_prepare_taxonomies'] ?? '')), true);
        $checks = [];
        foreach ($expected_taxonomies as $taxonomy => $expected_slugs) {
            if (!is_string($taxonomy) || !isset($allowed[$taxonomy]) || !taxonomy_exists($taxonomy)) {
                return new WP_Error('publication_taxonomy_not_allowed', 'Publication candidate requested a taxonomy outside the configured allowlist.');
            }
            if (!is_array($expected_slugs)) {
                return new WP_Error('invalid_publication_terms', 'Expected taxonomy values must be arrays of slugs.');
            }
            $clean_expected = [];
            foreach ($expected_slugs as $slug) {
                $clean = sanitize_title((string)$slug);
                if ($clean === '') {
                    return new WP_Error('invalid_publication_term_slug', 'Expected taxonomy term slugs must be non-empty.');
                }
                $clean_expected[] = $clean;
            }
            sort($clean_expected);
            $actual = wp_get_object_terms($post_id, $taxonomy, ['fields' => 'slugs']);
            if (is_wp_error($actual)) {
                return $actual;
            }
            $actual = array_map('strval', $actual);
            sort($actual);
            $checks[$taxonomy] = $actual === $clean_expected;
        }
        return $checks;
    }

    private function validate_envelope(array $body)
    {
        if ((int)($body['schema_version'] ?? 0) !== 1) {
            return new WP_Error('unsupported_schema', 'Unsupported relay request schema_version.');
        }
        $request_id = (string)($body['request_id'] ?? '');
        if (!preg_match('/^[a-zA-Z0-9._:-]{8,128}$/', $request_id)) {
            return new WP_Error('invalid_request_id', 'Invalid request_id.');
        }
        $connection_id = (string)($body['connection_id'] ?? '');
        if (!preg_match('/^[a-zA-Z0-9._-]{1,80}$/', $connection_id)) {
            return new WP_Error('invalid_connection_id', 'Invalid connection_id.');
        }
        $operation = (string)($body['operation'] ?? '');
        if (!in_array($operation, ['publication_preflight', 'article_publish', 'published_article_read'], true)) {
            return new WP_Error('invalid_operation', 'Invalid publication operation.');
        }
        $issued_at = strtotime((string)($body['issued_at'] ?? ''));
        if ($issued_at === false || abs(time() - $issued_at) > HOUR_IN_SECONDS) {
            return new WP_Error('stale_request', 'Relay request issued_at must be within one hour of server time.');
        }
        return true;
    }

    private function repository_path(string $value): string
    {
        $value = trim(str_replace('\\', '/', $value));
        if ($value === '' || strpos($value, '/') === 0 || strpos($value, "\0") !== false) {
            return '';
        }
        $parts = explode('/', $value);
        foreach ($parts as $part) {
            if ($part === '' || $part === '.' || $part === '..') {
                return '';
            }
        }
        return preg_match('/^[A-Za-z0-9._\/@+,:=\-]+(?:\/[A-Za-z0-9._\/@+,:=\-]+)*$/', $value) ? $value : '';
    }

    private function csv_list(string $value): array
    {
        $items = preg_split('/[\r\n,]+/', $value) ?: [];
        $out = [];
        foreach ($items as $item) {
            $item = trim((string)$item);
            if ($item !== '') {
                $out[] = $item;
            }
        }
        return array_values(array_unique($out));
    }

    private function settings(): array
    {
        $settings = get_option(self::OPTION, []);
        return is_array($settings) ? $settings : [];
    }

    private function request_seen(string $request_id): bool
    {
        $seen = get_option('seo_workflow_bridge_seen_requests', []);
        if (!is_array($seen)) {
            $seen = [];
        }
        $this->purge_seen($seen);
        return isset($seen[hash('sha256', $request_id)]);
    }

    private function mark_request_seen(string $request_id): void
    {
        $seen = get_option('seo_workflow_bridge_seen_requests', []);
        if (!is_array($seen)) {
            $seen = [];
        }
        $this->purge_seen($seen);
        $seen[hash('sha256', $request_id)] = time();
        update_option('seo_workflow_bridge_seen_requests', $seen, false);
    }

    private function purge_seen(array &$seen): void
    {
        $cutoff = time() - self::REQUEST_TTL;
        foreach ($seen as $key => $timestamp) {
            if ((int)$timestamp < $cutoff) {
                unset($seen[$key]);
            }
        }
    }

    private function error(string $code, string $message, int $status, string $request_id = ''): WP_REST_Response
    {
        $body = ['ok' => false, 'schema_version' => 1, 'error' => ['code' => $code, 'message' => $message]];
        if ($request_id !== '') {
            $body['request_id'] = $request_id;
        }
        return new WP_REST_Response($body, $status);
    }
}
