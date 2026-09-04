<?php

declare(strict_types=1);

if (!defined('ABSPATH')) {
    exit;
}

final class SEO_Workflow_Bridge_LinkedIn_Scheduled_Publish
{
    private const BRIDGE_OPTION = 'seo_workflow_bridge_settings';
    private const LINKEDIN_SETTINGS_OPTION = 'seo_workflow_bridge_linkedin_settings';
    private const TOKEN_OPTION = 'seo_workflow_bridge_linkedin_token';
    private const IDENTITY_OPTION = 'seo_workflow_bridge_linkedin_identity';
    private const RESULT_OPTION = 'seo_workflow_bridge_linkedin_scheduled_results';
    private const REQUEST_TTL = 86400;
    private const POSTS_URL = 'https://api.linkedin.com/rest/posts';
    private const IMAGES_URL = 'https://api.linkedin.com/rest/images?action=initializeUpload';
    private const LINKEDIN_VERSION = '202608';
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
            register_rest_route('seo-workflow-bridge/v1', '/linkedin/publish-authorized', [
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

        $linkedin = get_option(self::LINKEDIN_SETTINGS_OPTION, []);
        $linkedin = is_array($linkedin) ? $linkedin : [];
        if (empty($linkedin['enabled'])) {
            return $this->error('linkedin_disabled', 'LinkedIn publication capability is disabled.', 503);
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
        if (!empty($results[$post_id]['published'])) {
            $existing = $results[$post_id];
            return new WP_REST_Response([
                'ok' => true,
                'schema_version' => 2,
                'request_id' => $request_id,
                'result' => $existing,
                'idempotent_replay' => true,
            ], 200);
        }

        $planned_at = strtotime((string)$candidate['planned_at']);
        if ($planned_at === false || time() < $planned_at) {
            return $this->error('linkedin_not_due', 'This authorized post is not due yet.', 409);
        }
        if (time() - $planned_at > DAY_IN_SECONDS) {
            return $this->error('linkedin_schedule_stale', 'The publication window is more than 24 hours late and requires review.', 409);
        }

        $token = get_option(self::TOKEN_OPTION, []);
        $token = is_array($token) ? $token : [];
        $identity = get_option(self::IDENTITY_OPTION, []);
        $identity = is_array($identity) ? $identity : [];
        $access_token = (string)($token['access_token'] ?? '');
        $expires_at = (int)($token['expires_at'] ?? 0);
        $subject = trim((string)($identity['sub'] ?? ''));
        if ($access_token === '' || $expires_at <= time() || $subject === '') {
            return $this->error('linkedin_connection_invalid', 'LinkedIn token or verified member identity is missing or expired.', 409);
        }

        $expected_author = 'urn:li:person:' . $subject;
        if (!hash_equals($expected_author, (string)$candidate['author_urn'])) {
            return $this->error('linkedin_author_drift', 'The authorized LinkedIn author no longer matches the connected member.', 409);
        }

        $text = (string)$candidate['text'];
        $alt_text = (string)$candidate['alt_text'];
        if (!hash_equals((string)$candidate['text_sha256'], hash('sha256', $text))) {
            return $this->error('linkedin_text_drift', 'Text hash does not match the authorized text.', 409);
        }
        if (!hash_equals((string)$candidate['alt_text_sha256'], hash('sha256', $alt_text))) {
            return $this->error('linkedin_alt_text_drift', 'ALT text hash does not match the authorized ALT text.', 409);
        }

        $intent_sha256 = hash('sha256', $this->intent_material($candidate));
        if (!hash_equals((string)$candidate['intent_sha256'], $intent_sha256)) {
            return $this->error('linkedin_intent_drift', 'Publication intent hash no longer matches the preauthorized candidate.', 409);
        }

        $image = $this->fetch_delivery_image($candidate);
        if (is_wp_error($image)) {
            return $this->error($image->get_error_code(), $image->get_error_message(), 409);
        }

        $image_urn = $this->upload_linkedin_image($access_token, $expected_author, (string)$candidate['image_mime_type'], $image);
        if (is_wp_error($image_urn)) {
            return $this->error($image_urn->get_error_code(), $image_urn->get_error_message(), 502);
        }

        $linkedin_payload = [
            'author' => $expected_author,
            'commentary' => $text,
            'visibility' => 'PUBLIC',
            'distribution' => [
                'feedDistribution' => 'MAIN_FEED',
                'targetEntities' => [],
                'thirdPartyDistributionChannels' => [],
            ],
            'content' => [
                'media' => [
                    'altText' => $alt_text,
                    'id' => $image_urn,
                ],
            ],
            'lifecycleState' => 'PUBLISHED',
            'isReshareDisabledByAuthor' => false,
        ];
        $payload_json = wp_json_encode($linkedin_payload, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
        if (!is_string($payload_json) || $payload_json === '') {
            return $this->error('linkedin_payload_invalid', 'Unable to build LinkedIn payload.', 500);
        }
        $payload_sha256 = hash('sha256', $payload_json);

        $response = wp_remote_post(self::POSTS_URL, [
            'timeout' => 30,
            'redirection' => 0,
            'headers' => [
                'Accept' => 'application/json',
                'Authorization' => 'Bearer ' . $access_token,
                'Content-Type' => 'application/json',
                'Linkedin-Version' => self::LINKEDIN_VERSION,
                'X-Restli-Protocol-Version' => '2.0.0',
            ],
            'body' => $payload_json,
        ]);
        if (is_wp_error($response)) {
            return $this->error('linkedin_publish_request_failed', 'LinkedIn publication request failed.', 502);
        }

        $status = (int)wp_remote_retrieve_response_code($response);
        $headers = wp_remote_retrieve_headers($response);
        $remote_id = '';
        if (is_object($headers) && method_exists($headers, 'offsetGet')) {
            $remote_id = sanitize_text_field((string)$headers->offsetGet('x-restli-id'));
        } elseif (is_array($headers)) {
            $remote_id = sanitize_text_field((string)($headers['x-restli-id'] ?? ''));
        }
        if ($status !== 201 || $remote_id === '') {
            return $this->error('linkedin_publish_response_invalid', 'LinkedIn did not return HTTP 201 with x-restli-id.', 502);
        }

        $evidence = [
            'published' => true,
            'post_id' => $post_id,
            'authorization_id' => (string)$authorization['authorization_id'],
            'remote_post_id' => $remote_id,
            'published_at' => time(),
            'planned_at' => (string)$candidate['planned_at'],
            'author_urn' => $expected_author,
            'text_sha256' => (string)$candidate['text_sha256'],
            'image_sha256' => (string)$candidate['image_sha256'],
            'alt_text_sha256' => (string)$candidate['alt_text_sha256'],
            'delivery_provider' => (string)$candidate['delivery_provider'],
            'delivery_file_id' => (string)$candidate['delivery_file_id'],
            'image_urn' => $image_urn,
            'intent_sha256' => $intent_sha256,
            'payload_sha256' => $payload_sha256,
            'linkedin_version' => self::LINKEDIN_VERSION,
            'http_status' => 201,
            'github_run_id' => (string)($claims['run_id'] ?? ''),
        ];
        $results[$post_id] = $evidence;
        update_option(self::RESULT_OPTION, $results, false);
        $this->mark_request_seen($request_id);

        return new WP_REST_Response([
            'ok' => true,
            'schema_version' => 2,
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
        if ((string)($body['operation'] ?? '') !== 'linkedin_publish_authorized') {
            return new WP_Error('invalid_operation', 'Expected linkedin_publish_authorized operation.');
        }
        if (!preg_match('/^[A-Za-z0-9._:-]{8,128}$/', (string)($body['request_id'] ?? ''))) {
            return new WP_Error('invalid_request_id', 'Invalid publication request_id.');
        }
        $issued_at = strtotime((string)($body['issued_at'] ?? ''));
        if ($issued_at === false || abs(time() - $issued_at) > HOUR_IN_SECONDS) {
            return new WP_Error('stale_request', 'Publication request issued_at must be within one hour of server time.');
        }
        if (!is_array($body['payload'] ?? null) || (int)($body['payload']['schema_version'] ?? 0) !== 2) {
            return new WP_Error('invalid_payload', 'LinkedIn scheduled publication payload schema_version 2 is required.');
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
            'post_id', 'planned_at', 'author_urn', 'text', 'text_sha256', 'alt_text', 'alt_text_sha256',
            'image_sha256', 'image_mime_type', 'image_size_bytes', 'delivery_provider', 'delivery_file_id', 'intent_sha256',
        ];
        foreach ($required_candidate as $key) {
            if (!isset($candidate[$key]) || !is_string($candidate[$key]) || trim($candidate[$key]) === '') {
                return new WP_Error('linkedin_candidate_incomplete', 'Missing candidate field: ' . $key);
            }
        }
        $required_authorization = [
            'authorization_id', 'status', 'post_id', 'planned_at', 'author_urn', 'text_sha256', 'alt_text_sha256',
            'image_sha256', 'image_mime_type', 'image_size_bytes', 'delivery_provider', 'delivery_file_id', 'intent_sha256', 'authorized_at',
        ];
        foreach ($required_authorization as $key) {
            if (!isset($authorization[$key]) || !is_string($authorization[$key]) || trim($authorization[$key]) === '') {
                return new WP_Error('linkedin_authorization_incomplete', 'Missing authorization field: ' . $key);
            }
        }
        if ((string)$authorization['status'] !== 'authorized_for_scheduled_publication') {
            return new WP_Error('linkedin_not_preauthorized', 'Post is not preauthorized for scheduled LinkedIn publication.');
        }
        foreach ([
            'post_id', 'planned_at', 'author_urn', 'text_sha256', 'alt_text_sha256', 'image_sha256', 'image_mime_type',
            'image_size_bytes', 'delivery_provider', 'delivery_file_id', 'intent_sha256',
        ] as $key) {
            if (!hash_equals((string)$candidate[$key], (string)$authorization[$key])) {
                return new WP_Error('linkedin_authorization_drift', 'Authorization no longer matches candidate field: ' . $key);
            }
        }
        if (!preg_match('/^[A-Za-z0-9._:-]{8,160}$/', (string)$authorization['authorization_id'])) {
            return new WP_Error('linkedin_authorization_id_invalid', 'Invalid authorization_id.');
        }
        if (strtotime((string)$authorization['authorized_at']) === false || strtotime((string)$candidate['planned_at']) === false) {
            return new WP_Error('linkedin_authorization_invalid', 'authorized_at or planned_at is invalid.');
        }
        if (!preg_match('/^[a-zA-Z0-9][a-zA-Z0-9._-]{3,79}$/', (string)$candidate['post_id'])) {
            return new WP_Error('linkedin_post_id_invalid', 'Invalid post_id.');
        }
        foreach (['text_sha256', 'alt_text_sha256', 'image_sha256', 'intent_sha256'] as $hash_key) {
            if (!preg_match('/^[a-f0-9]{64}$/', (string)$candidate[$hash_key])) {
                return new WP_Error('linkedin_hash_invalid', 'Candidate hashes must be lowercase SHA-256 values.');
            }
        }
        if ((string)$candidate['delivery_provider'] !== self::DELIVERY_PROVIDER) {
            return new WP_Error('linkedin_delivery_provider_invalid', 'Unsupported scheduled media delivery provider.');
        }
        if (!preg_match('/^[A-Za-z0-9_-]{10,128}$/', (string)$candidate['delivery_file_id'])) {
            return new WP_Error('linkedin_delivery_file_invalid', 'Invalid Drive delivery file ID.');
        }
        if (!in_array((string)$candidate['image_mime_type'], ['image/png', 'image/jpeg'], true)) {
            return new WP_Error('linkedin_image_mime_invalid', 'Unsupported image MIME type.');
        }
        $size = (int)$candidate['image_size_bytes'];
        if ($size <= 0 || $size > self::MAX_IMAGE_BYTES) {
            return new WP_Error('linkedin_image_size_invalid', 'Image size is invalid or exceeds the Bridge limit.');
        }
        return true;
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
            return new WP_Error('linkedin_delivery_fetch_failed', 'Unable to fetch the temporary Drive delivery copy.');
        }
        $status = (int)wp_remote_retrieve_response_code($response);
        if ($status < 200 || $status >= 300) {
            return new WP_Error('linkedin_delivery_fetch_failed', 'Temporary Drive delivery copy returned HTTP ' . $status . '.');
        }
        $bytes = (string)wp_remote_retrieve_body($response);
        if (strlen($bytes) !== (int)$candidate['image_size_bytes']) {
            return new WP_Error('linkedin_delivery_size_drift', 'Delivery image byte size no longer matches the authorized image.');
        }
        if (!hash_equals((string)$candidate['image_sha256'], hash('sha256', $bytes))) {
            return new WP_Error('linkedin_delivery_hash_drift', 'Delivery image SHA-256 no longer matches the authorized final image.');
        }
        $detected = $this->detect_image_mime($bytes);
        if ($detected === '' || !hash_equals((string)$candidate['image_mime_type'], $detected)) {
            return new WP_Error('linkedin_delivery_mime_drift', 'Delivery image MIME no longer matches the authorized image.');
        }
        return $bytes;
    }

    /** @return string|WP_Error */
    private function upload_linkedin_image(string $access_token, string $owner, string $mime_type, string $bytes)
    {
        $init = wp_remote_post(self::IMAGES_URL, [
            'timeout' => 20,
            'redirection' => 0,
            'headers' => [
                'Accept' => 'application/json',
                'Authorization' => 'Bearer ' . $access_token,
                'Content-Type' => 'application/json',
                'Linkedin-Version' => self::LINKEDIN_VERSION,
                'X-Restli-Protocol-Version' => '2.0.0',
            ],
            'body' => wp_json_encode(['initializeUploadRequest' => ['owner' => $owner]]),
        ]);
        if (is_wp_error($init)) {
            return new WP_Error('linkedin_image_initialize_failed', 'LinkedIn image initialization failed.');
        }
        $status = (int)wp_remote_retrieve_response_code($init);
        $body = json_decode((string)wp_remote_retrieve_body($init), true);
        $image_urn = is_array($body) ? sanitize_text_field((string)($body['value']['image'] ?? '')) : '';
        $upload_url = is_array($body) ? (string)($body['value']['uploadUrl'] ?? '') : '';
        if ($status < 200 || $status >= 300 || !preg_match('/^urn:li:image:[A-Za-z0-9_-]+$/', $image_urn) || stripos($upload_url, 'https://') !== 0) {
            return new WP_Error('linkedin_image_initialize_failed', 'LinkedIn did not return a valid image upload target.');
        }

        $upload = wp_remote_request($upload_url, [
            'method' => 'PUT',
            'timeout' => 30,
            'redirection' => 0,
            'headers' => ['Content-Type' => $mime_type],
            'body' => $bytes,
        ]);
        if (is_wp_error($upload)) {
            return new WP_Error('linkedin_image_upload_failed', 'LinkedIn image upload failed.');
        }
        $upload_status = (int)wp_remote_retrieve_response_code($upload);
        if ($upload_status < 200 || $upload_status >= 300) {
            return new WP_Error('linkedin_image_upload_failed', 'LinkedIn image upload returned HTTP ' . $upload_status . '.');
        }
        return $image_urn;
    }

    private function intent_material(array $candidate): string
    {
        return implode("\n", [
            (string)$candidate['post_id'],
            (string)$candidate['planned_at'],
            (string)$candidate['author_urn'],
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
        return (bool)get_transient('seo_workflow_bridge_linkedin_req_' . hash('sha256', $request_id));
    }

    private function mark_request_seen(string $request_id): void
    {
        set_transient('seo_workflow_bridge_linkedin_req_' . hash('sha256', $request_id), 1, self::REQUEST_TTL);
    }

    private function error(string $code, string $message, int $status): WP_REST_Response
    {
        return new WP_REST_Response(['ok' => false, 'error' => ['code' => $code, 'message' => $message]], $status);
    }
}
