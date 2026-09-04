<?php

declare(strict_types=1);

if (!defined('ABSPATH')) {
    exit;
}

final class SEO_Workflow_Bridge_Facebook_Page_Scheduled_Publish
{
    private const BRIDGE_OPTION = 'seo_workflow_bridge_settings';
    private const FACEBOOK_SETTINGS_OPTION = 'seo_workflow_bridge_facebook_page_settings';
    private const FACEBOOK_IDENTITY_OPTION = 'seo_workflow_bridge_facebook_page_identity';
    private const RESULT_OPTION = 'seo_workflow_bridge_facebook_page_scheduled_results';
    private const REQUEST_TTL = 86400;
    private const GRAPH_API_VERSION = 'v26.0';
    private const DELIVERY_PROVIDER = 'google_drive_tmp_outbox';
    private const MAX_IMAGE_BYTES = 10_000_000;

    private SEO_Workflow_Bridge_OIDC_Verifier $verifier;

    public function __construct(SEO_Workflow_Bridge_OIDC_Verifier $verifier)
    {
        $this->verifier = $verifier;
    }

    public function register(): void
    {
        add_action('rest_api_init', function (): void {
            register_rest_route('seo-workflow-bridge/v1', '/facebook/publish-authorized', [
                'methods' => 'POST',
                'callback' => [$this, 'publish'],
                'permission_callback' => '__return_true',
            ]);
        });
    }

    public function publish(WP_REST_Request $request): WP_REST_Response
    {
        $bridge = get_option(self::BRIDGE_OPTION, []);
        $bridge = is_array($bridge) ? $bridge : [];
        if (empty($bridge['enabled'])) {
            return $this->error('bridge_disabled', 'SEO Workflow Bridge is disabled.', 503);
        }

        $settings = get_option(self::FACEBOOK_SETTINGS_OPTION, []);
        $settings = is_array($settings) ? $settings : [];
        if (empty($settings['enabled'])) {
            return $this->error('facebook_page_disabled', 'Facebook Page publication capability is disabled.', 503);
        }

        $authorization_header = (string)$request->get_header('authorization');
        if (!preg_match('/^Bearer\s+(.+)$/i', $authorization_header, $matches)) {
            return $this->error('missing_bearer_token', 'A GitHub Actions OIDC bearer token is required.', 401);
        }
        $claims = $this->verifier->verify(trim($matches[1]), $bridge);
        if (is_wp_error($claims)) {
            return $this->error($claims->get_error_code(), $claims->get_error_message(), 401);
        }

        $body = $request->get_json_params();
        if (!is_array($body)) {
            return $this->error('invalid_request', 'Request body must be a JSON object.', 400);
        }
        $validated = $this->validate_request($body);
        if (is_wp_error($validated)) {
            return $this->error($validated->get_error_code(), $validated->get_error_message(), 400);
        }

        $request_id = (string)$body['request_id'];
        if ($this->request_seen($request_id)) {
            return $this->error('replayed_request', 'This publication request_id has already been processed.', 409);
        }

        $payload = $body['payload'];
        $candidate = $payload['candidate'];
        $authorization = $payload['authorization'];
        if (!is_array($candidate) || !is_array($authorization)) {
            return $this->error('invalid_candidate', 'Candidate and authorization must be objects.', 400);
        }
        $binding = $this->validate_authorization_binding($candidate, $authorization);
        if (is_wp_error($binding)) {
            return $this->error($binding->get_error_code(), $binding->get_error_message(), 409);
        }

        $post_id = (string)$candidate['post_id'];
        $results = get_option(self::RESULT_OPTION, []);
        $results = is_array($results) ? $results : [];
        $existing = isset($results[$post_id]) && is_array($results[$post_id]) ? $results[$post_id] : [];
        if (!empty($existing['published'])) {
            return new WP_REST_Response([
                'ok' => true,
                'schema_version' => 1,
                'request_id' => $request_id,
                'result' => $existing,
                'idempotent_replay' => true,
            ], 200);
        }
        if (in_array((string)($existing['publication_state'] ?? ''), ['inflight', 'uncertain_external_result'], true)) {
            return $this->error(
                'facebook_page_publish_uncertain',
                'A prior Facebook Page publication request may already have reached Meta. Automatic retry is blocked pending human reconciliation.',
                409
            );
        }

        $planned_at = strtotime((string)$candidate['planned_at']);
        if ($planned_at === false || time() < $planned_at) {
            return $this->error('facebook_page_not_due', 'This authorized Facebook Page post is not due yet.', 409);
        }
        if (time() - $planned_at > DAY_IN_SECONDS) {
            return $this->error('facebook_page_schedule_stale', 'The publication window is more than 24 hours late and requires review.', 409);
        }

        $configured_page_id = trim((string)($settings['page_id'] ?? ''));
        $page_access_token = trim((string)($settings['page_access_token'] ?? ''));
        $identity = get_option(self::FACEBOOK_IDENTITY_OPTION, []);
        $identity = is_array($identity) ? $identity : [];
        $verified_page_id = trim((string)($identity['page_id'] ?? ''));
        if ($configured_page_id === '' || $page_access_token === '' || $verified_page_id === '') {
            return $this->error('facebook_page_connection_invalid', 'Facebook Page ID, token or verified identity is missing.', 409);
        }
        if (!hash_equals($configured_page_id, $verified_page_id) || !hash_equals($configured_page_id, (string)$candidate['page_id'])) {
            return $this->error('facebook_page_identity_drift', 'The authorized Page no longer matches the configured verified Page.', 409);
        }

        $runtime_identity = $this->fetch_page_identity($configured_page_id, $page_access_token);
        if (is_wp_error($runtime_identity)) {
            return $this->error($runtime_identity->get_error_code(), $runtime_identity->get_error_message(), 409);
        }
        if (!hash_equals($configured_page_id, (string)$runtime_identity['id'])) {
            return $this->error('facebook_page_identity_drift', 'Meta returned a different Page identity.', 409);
        }

        $text = (string)$candidate['text'];
        $alt_text = (string)$candidate['alt_text'];
        if (!hash_equals((string)$candidate['text_sha256'], hash('sha256', $text))) {
            return $this->error('facebook_page_text_drift', 'Text hash does not match the authorized text.', 409);
        }
        if (!hash_equals((string)$candidate['alt_text_sha256'], hash('sha256', $alt_text))) {
            return $this->error('facebook_page_alt_text_drift', 'ALT text hash does not match the authorized ALT text.', 409);
        }
        $intent_sha256 = hash('sha256', $this->intent_material($candidate));
        if (!hash_equals((string)$candidate['intent_sha256'], $intent_sha256)) {
            return $this->error('facebook_page_intent_drift', 'Publication intent hash no longer matches the preauthorized candidate.', 409);
        }

        $image = $this->fetch_delivery_image($candidate);
        if (is_wp_error($image)) {
            return $this->error($image->get_error_code(), $image->get_error_message(), 409);
        }

        // Persist a fail-closed marker before the external Meta mutation. If the PHP
        // process or relay disappears after this point, a later request will not
        // blindly create a duplicate Page post.
        $inflight = [
            'published' => false,
            'publication_state' => 'inflight',
            'platform' => 'facebook',
            'target_type' => 'facebook_page',
            'post_id' => $post_id,
            'authorization_id' => (string)$authorization['authorization_id'],
            'page_id' => $configured_page_id,
            'page_name' => (string)$runtime_identity['name'],
            'started_at' => time(),
            'planned_at' => (string)$candidate['planned_at'],
            'text_sha256' => (string)$candidate['text_sha256'],
            'image_sha256' => (string)$candidate['image_sha256'],
            'alt_text_sha256' => (string)$candidate['alt_text_sha256'],
            'delivery_provider' => (string)$candidate['delivery_provider'],
            'delivery_file_id' => (string)$candidate['delivery_file_id'],
            'intent_sha256' => $intent_sha256,
            'graph_api_version' => self::GRAPH_API_VERSION,
            'github_run_id' => (string)($claims['run_id'] ?? ''),
        ];
        $results[$post_id] = $inflight;
        update_option(self::RESULT_OPTION, $results, false);
        $persisted_before = get_option(self::RESULT_OPTION, []);
        $persisted_before = is_array($persisted_before) ? $persisted_before : [];
        if ((string)($persisted_before[$post_id]['publication_state'] ?? '') !== 'inflight' ||
            !hash_equals((string)$authorization['authorization_id'], (string)($persisted_before[$post_id]['authorization_id'] ?? ''))) {
            return $this->error(
                'facebook_page_state_persist_failed',
                'Unable to persist the Facebook Page inflight safety marker. Publication was not attempted.',
                500
            );
        }

        $remote = $this->create_page_photo(
            $configured_page_id,
            $page_access_token,
            $text,
            $alt_text,
            (string)$candidate['image_mime_type'],
            $image
        );
        if (is_wp_error($remote)) {
            $code = $remote->get_error_code();
            if ($code === 'facebook_page_publish_uncertain') {
                $results[$post_id] = array_merge($inflight, [
                    'publication_state' => 'uncertain_external_result',
                    'uncertain_at' => time(),
                    'last_error_code' => $code,
                ]);
                update_option(self::RESULT_OPTION, $results, false);
                return $this->error($code, $remote->get_error_message(), 502);
            }

            // A deterministic Meta rejection means no publication was created, so
            // remove the inflight marker and allow a later corrected exact attempt.
            unset($results[$post_id]);
            update_option(self::RESULT_OPTION, $results, false);
            return $this->error($code, $remote->get_error_message(), 409);
        }

        $evidence = [
            'published' => true,
            'publication_state' => 'published',
            'platform' => 'facebook',
            'target_type' => 'facebook_page',
            'post_id' => $post_id,
            'authorization_id' => (string)$authorization['authorization_id'],
            'page_id' => $configured_page_id,
            'page_name' => (string)$runtime_identity['name'],
            'remote_post_id' => (string)$remote['post_id'],
            'remote_media_id' => (string)$remote['media_id'],
            'published_at' => time(),
            'planned_at' => (string)$candidate['planned_at'],
            'text_sha256' => (string)$candidate['text_sha256'],
            'image_sha256' => (string)$candidate['image_sha256'],
            'alt_text_sha256' => (string)$candidate['alt_text_sha256'],
            'delivery_provider' => (string)$candidate['delivery_provider'],
            'delivery_file_id' => (string)$candidate['delivery_file_id'],
            'intent_sha256' => $intent_sha256,
            'graph_api_version' => self::GRAPH_API_VERSION,
            'http_status' => (int)$remote['http_status'],
            'github_run_id' => (string)($claims['run_id'] ?? ''),
        ];
        $results[$post_id] = $evidence;
        update_option(self::RESULT_OPTION, $results, false);

        // Treat remote success without durable Bridge evidence as uncertain. The
        // remote identifiers are returned for manual reconciliation if the relay
        // receives this response.
        $persisted_after = get_option(self::RESULT_OPTION, []);
        $persisted_after = is_array($persisted_after) ? $persisted_after : [];
        if (empty($persisted_after[$post_id]['published']) ||
            !hash_equals((string)$remote['media_id'], (string)($persisted_after[$post_id]['remote_media_id'] ?? ''))) {
            return new WP_REST_Response([
                'ok' => false,
                'error' => [
                    'code' => 'facebook_page_publish_uncertain',
                    'message' => 'Meta returned definitive creation evidence but the Bridge could not verify durable evidence persistence. Automatic retry is forbidden.',
                    'remote_post_id' => (string)$remote['post_id'],
                    'remote_media_id' => (string)$remote['media_id'],
                ],
            ], 502);
        }

        $this->mark_request_seen($request_id);

        return new WP_REST_Response([
            'ok' => true,
            'schema_version' => 1,
            'request_id' => $request_id,
            'result' => $evidence,
        ], 201);
    }

    /** @return true|WP_Error */
    private function validate_request(array $body)
    {
        if ((int)($body['schema_version'] ?? 0) !== 1) {
            return new WP_Error('unsupported_schema', 'Unsupported relay request schema_version.');
        }
        if ((string)($body['operation'] ?? '') !== 'facebook_page_publish_authorized') {
            return new WP_Error('invalid_operation', 'Expected facebook_page_publish_authorized operation.');
        }
        if (!preg_match('/^[A-Za-z0-9._:-]{8,128}$/', (string)($body['request_id'] ?? ''))) {
            return new WP_Error('invalid_request_id', 'Invalid publication request_id.');
        }
        $issued_at = strtotime((string)($body['issued_at'] ?? ''));
        if ($issued_at === false || abs(time() - $issued_at) > HOUR_IN_SECONDS) {
            return new WP_Error('stale_request', 'Publication request issued_at must be within one hour of server time.');
        }
        if (!is_array($body['payload'] ?? null) || (int)($body['payload']['schema_version'] ?? 0) !== 1) {
            return new WP_Error('invalid_payload', 'Facebook Page scheduled publication payload schema_version 1 is required.');
        }
        if (!is_array($body['payload']['candidate'] ?? null) || !is_array($body['payload']['authorization'] ?? null)) {
            return new WP_Error('invalid_candidate', 'candidate and authorization are required objects.');
        }
        return true;
    }

    /** @return true|WP_Error */
    private function validate_authorization_binding(array $candidate, array $authorization)
    {
        $required_candidate = [
            'post_id', 'planned_at', 'target_type', 'page_id', 'text', 'text_sha256', 'alt_text', 'alt_text_sha256',
            'image_sha256', 'image_mime_type', 'image_size_bytes', 'delivery_provider', 'delivery_file_id', 'intent_sha256',
        ];
        foreach ($required_candidate as $key) {
            if (!isset($candidate[$key]) || !is_string($candidate[$key]) || trim($candidate[$key]) === '') {
                return new WP_Error('facebook_page_candidate_incomplete', 'Missing candidate field: ' . $key);
            }
        }
        $required_authorization = [
            'authorization_id', 'status', 'post_id', 'planned_at', 'target_type', 'page_id', 'text_sha256', 'alt_text_sha256',
            'image_sha256', 'image_mime_type', 'image_size_bytes', 'delivery_provider', 'delivery_file_id', 'intent_sha256', 'authorized_at',
        ];
        foreach ($required_authorization as $key) {
            if (!isset($authorization[$key]) || !is_string($authorization[$key]) || trim($authorization[$key]) === '') {
                return new WP_Error('facebook_page_authorization_incomplete', 'Missing authorization field: ' . $key);
            }
        }
        if ((string)$candidate['target_type'] !== 'facebook_page' || (string)$authorization['target_type'] !== 'facebook_page') {
            return new WP_Error('facebook_page_target_invalid', 'Only facebook_page targets are supported.');
        }
        if ((string)$authorization['status'] !== 'authorized_for_scheduled_publication') {
            return new WP_Error('facebook_page_not_preauthorized', 'Post is not preauthorized for scheduled Facebook Page publication.');
        }
        foreach ([
            'post_id', 'planned_at', 'target_type', 'page_id', 'text_sha256', 'alt_text_sha256', 'image_sha256',
            'image_mime_type', 'image_size_bytes', 'delivery_provider', 'delivery_file_id', 'intent_sha256',
        ] as $key) {
            if (!hash_equals((string)$candidate[$key], (string)$authorization[$key])) {
                return new WP_Error('facebook_page_authorization_drift', 'Authorization no longer matches candidate field: ' . $key);
            }
        }
        if (!preg_match('/^[0-9]{5,32}$/', (string)$candidate['page_id'])) {
            return new WP_Error('facebook_page_id_invalid', 'Facebook Page ID must be numeric.');
        }
        if (!preg_match('/^[a-zA-Z0-9][a-zA-Z0-9._-]{3,79}$/', (string)$candidate['post_id'])) {
            return new WP_Error('facebook_page_post_id_invalid', 'Invalid post_id.');
        }
        if (!preg_match('/^[A-Za-z0-9._:-]{8,160}$/', (string)$authorization['authorization_id'])) {
            return new WP_Error('facebook_page_authorization_id_invalid', 'Invalid authorization_id.');
        }
        if (strtotime((string)$authorization['authorized_at']) === false || strtotime((string)$candidate['planned_at']) === false) {
            return new WP_Error('facebook_page_authorization_invalid', 'authorized_at or planned_at is invalid.');
        }
        foreach (['text_sha256', 'alt_text_sha256', 'image_sha256', 'intent_sha256'] as $hash_key) {
            if (!preg_match('/^[a-f0-9]{64}$/', (string)$candidate[$hash_key])) {
                return new WP_Error('facebook_page_hash_invalid', 'Candidate hashes must be lowercase SHA-256 values.');
            }
        }
        if ((string)$candidate['delivery_provider'] !== self::DELIVERY_PROVIDER) {
            return new WP_Error('facebook_page_delivery_provider_invalid', 'Unsupported scheduled media delivery provider.');
        }
        if (!preg_match('/^[A-Za-z0-9_-]{10,128}$/', (string)$candidate['delivery_file_id'])) {
            return new WP_Error('facebook_page_delivery_file_invalid', 'Invalid Drive delivery file ID.');
        }
        if (!in_array((string)$candidate['image_mime_type'], ['image/png', 'image/jpeg'], true)) {
            return new WP_Error('facebook_page_image_mime_invalid', 'Unsupported image MIME type.');
        }
        $size = (int)$candidate['image_size_bytes'];
        if ($size <= 0 || $size > self::MAX_IMAGE_BYTES) {
            return new WP_Error('facebook_page_image_size_invalid', 'Image size is invalid or exceeds the Bridge limit.');
        }
        return true;
    }

    /** @return array<string,string>|WP_Error */
    private function fetch_page_identity(string $page_id, string $token)
    {
        $url = 'https://graph.facebook.com/' . self::GRAPH_API_VERSION . '/' . rawurlencode($page_id) . '?fields=id,name';
        $response = wp_remote_get($url, [
            'timeout' => 20,
            'redirection' => 0,
            'headers' => ['Accept' => 'application/json', 'Authorization' => 'Bearer ' . $token],
            'user-agent' => 'SEO-Workflow-Bridge/' . SEO_WORKFLOW_BRIDGE_VERSION,
        ]);
        if (is_wp_error($response)) {
            return new WP_Error('facebook_page_runtime_verify_failed', 'Unable to verify the configured Facebook Page immediately before publication.');
        }
        $status = (int)wp_remote_retrieve_response_code($response);
        $body = json_decode((string)wp_remote_retrieve_body($response), true);
        if ($status !== 200 || !is_array($body) || empty($body['id']) || empty($body['name'])) {
            return new WP_Error('facebook_page_runtime_verify_failed', 'Meta rejected the configured Facebook Page token or identity.');
        }
        return ['id' => sanitize_text_field((string)$body['id']), 'name' => sanitize_text_field((string)$body['name'])];
    }

    /** @return string|WP_Error */
    private function fetch_delivery_image(array $candidate)
    {
        $file_id = (string)$candidate['delivery_file_id'];
        $url = 'https://drive.usercontent.google.com/download?id=' . rawurlencode($file_id) . '&export=download&confirm=t';
        $response = wp_remote_get($url, [
            'timeout' => 30,
            'redirection' => 3,
            'limit_response_size' => self::MAX_IMAGE_BYTES + 1,
            'headers' => ['Accept' => '*/*'],
        ]);
        if (is_wp_error($response)) {
            return new WP_Error('facebook_page_delivery_fetch_failed', 'Unable to fetch the temporary Drive delivery copy.');
        }
        $status = (int)wp_remote_retrieve_response_code($response);
        if ($status < 200 || $status >= 300) {
            return new WP_Error('facebook_page_delivery_fetch_failed', 'Temporary Drive delivery copy returned HTTP ' . $status . '.');
        }
        $bytes = (string)wp_remote_retrieve_body($response);
        if (strlen($bytes) !== (int)$candidate['image_size_bytes']) {
            return new WP_Error('facebook_page_delivery_size_drift', 'Delivery image byte size no longer matches the authorized image.');
        }
        if (!hash_equals((string)$candidate['image_sha256'], hash('sha256', $bytes))) {
            return new WP_Error('facebook_page_delivery_hash_drift', 'Delivery image SHA-256 no longer matches the authorized final image.');
        }
        $detected = $this->detect_image_mime($bytes);
        if ($detected === '' || !hash_equals((string)$candidate['image_mime_type'], $detected)) {
            return new WP_Error('facebook_page_delivery_mime_drift', 'Delivery image MIME no longer matches the authorized image.');
        }
        return $bytes;
    }

    /** @return array<string,mixed>|WP_Error */
    private function create_page_photo(string $page_id, string $token, string $caption, string $alt_text, string $mime_type, string $bytes)
    {
        try {
            $boundary = '----------------seo-workflow-bridge-' . bin2hex(random_bytes(12));
        } catch (Exception $exc) {
            return new WP_Error('facebook_page_publish_prepare_failed', 'Unable to prepare a secure multipart publication request.');
        }
        $extension = $mime_type === 'image/png' ? 'png' : 'jpg';
        $body = '';
        foreach (['caption' => $caption, 'alt_text_custom' => $alt_text, 'published' => 'true'] as $name => $value) {
            $body .= '--' . $boundary . "\r\n";
            $body .= 'Content-Disposition: form-data; name="' . $name . '"' . "\r\n\r\n";
            $body .= $value . "\r\n";
        }
        $body .= '--' . $boundary . "\r\n";
        $body .= 'Content-Disposition: form-data; name="source"; filename="social-image.' . $extension . '"' . "\r\n";
        $body .= 'Content-Type: ' . $mime_type . "\r\n\r\n";
        $body .= $bytes . "\r\n";
        $body .= '--' . $boundary . "--\r\n";

        $url = 'https://graph.facebook.com/' . self::GRAPH_API_VERSION . '/' . rawurlencode($page_id) . '/photos';
        $response = wp_remote_post($url, [
            'timeout' => 45,
            'redirection' => 0,
            'headers' => [
                'Accept' => 'application/json',
                'Authorization' => 'Bearer ' . $token,
                'Content-Type' => 'multipart/form-data; boundary=' . $boundary,
            ],
            'body' => $body,
            'data_format' => 'body',
            'user-agent' => 'SEO-Workflow-Bridge/' . SEO_WORKFLOW_BRIDGE_VERSION,
        ]);
        if (is_wp_error($response)) {
            return new WP_Error('facebook_page_publish_uncertain', 'Meta publication transport failed after the external request began. Automatic blind retry is forbidden.');
        }

        $status = (int)wp_remote_retrieve_response_code($response);
        $decoded = json_decode((string)wp_remote_retrieve_body($response), true);
        if ($status >= 500) {
            return new WP_Error('facebook_page_publish_uncertain', 'Meta returned a server error after the external request began. Automatic blind retry is forbidden.');
        }
        if ($status < 200 || $status >= 300 || !is_array($decoded)) {
            return new WP_Error('facebook_page_publish_rejected', 'Meta rejected the Facebook Page photo publication request.');
        }
        $media_id = sanitize_text_field((string)($decoded['id'] ?? ''));
        $post_id = sanitize_text_field((string)($decoded['post_id'] ?? ''));
        if ($media_id === '') {
            return new WP_Error('facebook_page_publish_uncertain', 'Meta returned success without a media identifier. Automatic blind retry is forbidden.');
        }
        if ($post_id === '') {
            $post_id = $media_id;
        }
        return ['media_id' => $media_id, 'post_id' => $post_id, 'http_status' => $status];
    }

    private function intent_material(array $candidate): string
    {
        return implode("\n", [
            (string)$candidate['post_id'],
            (string)$candidate['planned_at'],
            (string)$candidate['target_type'],
            (string)$candidate['page_id'],
            (string)$candidate['text_sha256'],
            (string)$candidate['image_sha256'],
            (string)$candidate['alt_text_sha256'],
            (string)$candidate['image_mime_type'],
            (string)$candidate['image_size_bytes'],
            (string)$candidate['delivery_provider'],
            (string)$candidate['delivery_file_id'],
        ]);
    }

    private function detect_image_mime(string $bytes): string
    {
        if (substr($bytes, 0, 8) === "\x89PNG\r\n\x1a\n") {
            return 'image/png';
        }
        if (substr($bytes, 0, 3) === "\xff\xd8\xff") {
            return 'image/jpeg';
        }
        return '';
    }

    private function request_seen(string $request_id): bool
    {
        return (bool)get_transient('seo_workflow_bridge_facebook_req_' . hash('sha256', $request_id));
    }

    private function mark_request_seen(string $request_id): void
    {
        set_transient('seo_workflow_bridge_facebook_req_' . hash('sha256', $request_id), 1, self::REQUEST_TTL);
    }

    private function error(string $code, string $message, int $status): WP_REST_Response
    {
        return new WP_REST_Response(['ok' => false, 'error' => ['code' => $code, 'message' => $message]], $status);
    }
}
