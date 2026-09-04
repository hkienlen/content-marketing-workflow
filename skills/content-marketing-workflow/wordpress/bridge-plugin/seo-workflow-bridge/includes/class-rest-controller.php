<?php

declare(strict_types=1);

if (!defined('ABSPATH')) {
    exit;
}

final class SEO_Workflow_Bridge_REST_Controller
{
    private const OPTION = 'seo_workflow_bridge_settings';
    private const REQUEST_TTL = 86400;

    private SEO_Workflow_Bridge_OIDC_Verifier $verifier;

    public function __construct(SEO_Workflow_Bridge_OIDC_Verifier $verifier)
    {
        $this->verifier = $verifier;
    }

    public function register(): void
    {
        add_action('rest_api_init', function (): void {
            register_rest_route('seo-workflow-bridge/v1', '/execute', [
                'methods' => 'POST',
                'callback' => [$this, 'execute'],
                'permission_callback' => '__return_true',
            ]);
            register_rest_route('seo-workflow-bridge/v1', '/status', [
                'methods' => 'GET',
                'callback' => [$this, 'status'],
                'permission_callback' => static function (): bool {
                    return current_user_can('manage_options');
                },
            ]);
        });
    }

    public function status(WP_REST_Request $request): WP_REST_Response
    {
        unset($request);
        $settings = $this->settings();
        return new WP_REST_Response([
            'plugin_version' => SEO_WORKFLOW_BRIDGE_VERSION,
            'enabled' => !empty($settings['enabled']),
            'repository_id_configured' => !empty($settings['repository_id']),
            'workflow_ref_configured' => !empty($settings['workflow_ref']),
            'audience_configured' => !empty($settings['audience']),
            'content_read_enabled' => !empty($settings['allow_content_read']),
            'connection_test_writes_enabled' => !empty($settings['allow_connection_test_writes']),
        ], 200);
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

    /** @return array<string,mixed>|WP_Error */
    private function dispatch(string $operation, array $payload, array $settings)
    {
        switch ($operation) {
            case 'site_info':
                return $this->site_info();
            case 'social_connection_health':
                return $this->social_connection_health();
            case 'content_list':
                if (empty($settings['allow_content_read'])) {
                    return new WP_Error('content_read_disabled', 'Content read is disabled in the bridge settings.');
                }
                return $this->content_list($payload);
            case 'reference_read':
                if (empty($settings['allow_content_read'])) {
                    return new WP_Error('content_read_disabled', 'Content read is disabled in the bridge settings.');
                }
                return $this->reference_read($payload, $settings);
            case 'draft_create':
                if (empty($settings['allow_connection_test_writes'])) {
                    return new WP_Error('connection_test_writes_disabled', 'Connection-test draft writes are disabled.');
                }
                return $this->draft_create($payload);
            case 'draft_read':
                if (empty($settings['allow_content_read'])) {
                    return new WP_Error('content_read_disabled', 'Content read is disabled in the bridge settings.');
                }
                return $this->draft_read($payload);
            case 'draft_delete':
                if (empty($settings['allow_connection_test_writes'])) {
                    return new WP_Error('connection_test_writes_disabled', 'Connection-test draft writes are disabled.');
                }
                return $this->draft_delete($payload);
            default:
                return new WP_Error('unsupported_operation', 'Unsupported relay operation.');
        }
    }

    /** @return array<string,mixed> */
    private function site_info(): array
    {
        return [
            'site_url' => site_url(),
            'home_url' => home_url(),
            'core_version' => get_bloginfo('version'),
            'blog_public' => (string)get_option('blog_public'),
            'timezone' => wp_timezone_string(),
            'bridge_version' => defined('SEO_WORKFLOW_BRIDGE_VERSION') ? SEO_WORKFLOW_BRIDGE_VERSION : null,
            'linkedin' => class_exists('SEO_Workflow_Bridge_LinkedIn_Controller') ? SEO_Workflow_Bridge_LinkedIn_Controller::status() : ['available' => false],
            'facebook' => class_exists('SEO_Workflow_Bridge_Facebook_Page_Controller') ? SEO_Workflow_Bridge_Facebook_Page_Controller::status() : ['available' => false],
        ];
    }

    /** @return array<string,mixed> */
    private function social_connection_health(): array
    {
        return [
            'checked_at' => time(),
            'linkedin' => class_exists('SEO_Workflow_Bridge_LinkedIn_Controller') ? SEO_Workflow_Bridge_LinkedIn_Controller::health_status() : ['available' => false, 'credential_live_valid' => false],
            'facebook' => class_exists('SEO_Workflow_Bridge_Facebook_Page_Controller') ? SEO_Workflow_Bridge_Facebook_Page_Controller::health_status() : ['available' => false, 'credential_live_valid' => false],
        ];
    }

    /** @return array<string,mixed> */
    private function content_list(array $payload): array
    {
        $limit = min(max((int)($payload['limit'] ?? 5), 1), 10);
        $post_type = in_array(($payload['post_type'] ?? 'post'), ['post', 'page'], true)
            ? (string)$payload['post_type']
            : 'post';
        $posts = get_posts([
            'post_type' => $post_type,
            'post_status' => ['publish', 'draft', 'pending', 'private', 'future'],
            'numberposts' => $limit,
            'orderby' => 'modified',
            'order' => 'DESC',
            'suppress_filters' => false,
        ]);
        $items = [];
        foreach ($posts as $post) {
            $items[] = [
                'id' => (int)$post->ID,
                'post_type' => (string)$post->post_type,
                'status' => (string)$post->post_status,
                'slug' => (string)$post->post_name,
                'title' => get_the_title($post),
                'modified_gmt' => (string)$post->post_modified_gmt,
            ];
        }
        return ['items' => $items];
    }

    /** @return array<string,mixed>|WP_Error */
    private function reference_read(array $payload, array $settings)
    {
        $post_id = (int)($payload['id'] ?? 0);
        if ($post_id <= 0) {
            return new WP_Error('invalid_reference_id', 'A positive reference post ID is required.');
        }
        $post = get_post($post_id);
        if (!$post instanceof WP_Post) {
            return new WP_Error('reference_not_found', 'Reference content was not found.');
        }
        if (!in_array((string)$post->post_type, ['post', 'page'], true)) {
            return new WP_Error('unsupported_reference_type', 'Reference content must be a WordPress post or page.');
        }
        if (!in_array((string)$post->post_status, ['publish', 'draft', 'pending', 'private', 'future'], true)) {
            return new WP_Error('unsupported_reference_status', 'Reference content status is not readable by this operation.');
        }

        $requested_meta = $payload['meta_keys'] ?? [];
        if (!is_array($requested_meta)) {
            return new WP_Error('invalid_reference_meta_keys', 'meta_keys must be an array.');
        }
        if (count($requested_meta) > 32) {
            return new WP_Error('too_many_reference_meta_keys', 'At most 32 reference meta keys may be requested.');
        }

        $allowed_meta = array_fill_keys($this->csv_list((string)($settings['allowed_prepare_meta_keys'] ?? '')), true);
        $meta = [];
        foreach ($requested_meta as $raw_key) {
            if (!is_string($raw_key) || !preg_match('/^[A-Za-z0-9_.:-]{1,191}$/', $raw_key)) {
                return new WP_Error('invalid_reference_meta_key', 'Reference meta keys must use safe WordPress meta-key characters.');
            }
            if (!isset($allowed_meta[$raw_key])) {
                return new WP_Error('reference_meta_not_allowed', 'Reference meta key is not allowed by bridge settings: ' . $raw_key);
            }
            $value = get_post_meta($post_id, $raw_key, true);
            if (is_array($value) || is_object($value) || is_resource($value)) {
                return new WP_Error('reference_meta_value_unsupported', 'Reference meta value is non-scalar and is not exposed by this operation: ' . $raw_key);
            }
            $meta[$raw_key] = $value;
        }

        return [
            'id' => $post_id,
            'post_type' => (string)$post->post_type,
            'status' => (string)$post->post_status,
            'slug' => (string)$post->post_name,
            'title' => (string)$post->post_title,
            'excerpt' => (string)$post->post_excerpt,
            'content' => (string)$post->post_content,
            'author_id' => (int)$post->post_author,
            'featured_media_id' => (int)get_post_thumbnail_id($post_id),
            'modified_gmt' => (string)$post->post_modified_gmt,
            'post_meta' => $meta,
        ];
    }

    /** @return array<string,mixed>|WP_Error */
    private function draft_create(array $payload)
    {
        $title = sanitize_text_field((string)($payload['title'] ?? ''));
        $slug = sanitize_title((string)($payload['slug'] ?? ''));
        if ($title === '' || strpos($title, 'AI connection test ') !== 0) {
            return new WP_Error('invalid_test_title', 'Connection-test draft title must start with "AI connection test ".');
        }
        if ($slug === '' || strpos($slug, 'ai-connection-test-') !== 0) {
            return new WP_Error('invalid_test_slug', 'Connection-test draft slug must start with "ai-connection-test-".');
        }

        $post_id = wp_insert_post([
            'post_type' => 'post',
            'post_status' => 'draft',
            'post_title' => $title,
            'post_name' => $slug,
            'post_content' => sanitize_textarea_field((string)($payload['content'] ?? 'Temporary connection verification draft.')),
            'post_author' => 0,
        ], true);
        if (is_wp_error($post_id)) {
            return $post_id;
        }
        update_post_meta((int)$post_id, '_seo_workflow_bridge_test', '1');

        return [
            'id' => (int)$post_id,
            'status' => 'draft',
            'slug' => get_post_field('post_name', (int)$post_id),
            'title' => get_the_title((int)$post_id),
        ];
    }

    /** @return array<string,mixed>|WP_Error */
    private function draft_read(array $payload)
    {
        $post_id = (int)($payload['id'] ?? 0);
        $post = get_post($post_id);
        if (!$post instanceof WP_Post) {
            return new WP_Error('draft_not_found', 'Draft not found.');
        }
        if ($post->post_status !== 'draft' || get_post_meta($post_id, '_seo_workflow_bridge_test', true) !== '1') {
            return new WP_Error('not_test_draft', 'Only bridge-created connection-test drafts can be read by this operation.');
        }
        return [
            'id' => $post_id,
            'status' => (string)$post->post_status,
            'slug' => (string)$post->post_name,
            'title' => (string)$post->post_title,
            'content' => (string)$post->post_content,
        ];
    }

    /** @return array<string,mixed>|WP_Error */
    private function draft_delete(array $payload)
    {
        $post_id = (int)($payload['id'] ?? 0);
        $post = get_post($post_id);
        if (!$post instanceof WP_Post) {
            return new WP_Error('draft_not_found', 'Draft not found.');
        }
        if ($post->post_status !== 'draft' || get_post_meta($post_id, '_seo_workflow_bridge_test', true) !== '1') {
            return new WP_Error('not_test_draft', 'Only bridge-created connection-test drafts can be permanently deleted by this operation.');
        }
        $deleted = wp_delete_post($post_id, true);
        if (!$deleted) {
            return new WP_Error('draft_delete_failed', 'Unable to permanently delete the connection-test draft.');
        }
        return ['id' => $post_id, 'deleted' => get_post($post_id) === null];
    }

    /** @return true|WP_Error */
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
        if (!in_array($operation, ['site_info', 'social_connection_health', 'content_list', 'reference_read', 'draft_create', 'draft_read', 'draft_delete'], true)) {
            return new WP_Error('invalid_operation', 'Invalid relay operation.');
        }
        $issued_at = strtotime((string)($body['issued_at'] ?? ''));
        if ($issued_at === false || abs(time() - $issued_at) > HOUR_IN_SECONDS) {
            return new WP_Error('stale_request', 'Relay request issued_at must be within one hour of server time.');
        }
        return true;
    }

    /** @return list<string> */
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

    /** @return array<string,mixed> */
    private function settings(): array
    {
        $settings = get_option(self::OPTION, []);
        return is_array($settings) ? $settings : [];
    }

    private function error(string $code, string $message, int $status, string $request_id = ''): WP_REST_Response
    {
        return new WP_REST_Response([
            'ok' => false,
            'schema_version' => 1,
            'request_id' => $request_id,
            'error' => ['code' => $code, 'message' => $message],
        ], $status);
    }
}
