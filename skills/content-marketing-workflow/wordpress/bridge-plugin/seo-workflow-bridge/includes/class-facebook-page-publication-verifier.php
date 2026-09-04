<?php

declare(strict_types=1);

if (!defined('ABSPATH')) {
    exit;
}

final class SEO_Workflow_Bridge_Facebook_Page_Publication_Verifier
{
    private const BRIDGE_OPTION = 'seo_workflow_bridge_settings';
    private const FACEBOOK_SETTINGS_OPTION = 'seo_workflow_bridge_facebook_page_settings';
    private const FACEBOOK_IDENTITY_OPTION = 'seo_workflow_bridge_facebook_page_identity';
    private const RESULT_OPTION = 'seo_workflow_bridge_facebook_page_scheduled_results';
    private const GRAPH_API_VERSION = 'v26.0';

    private SEO_Workflow_Bridge_OIDC_Verifier $verifier;

    public function __construct(SEO_Workflow_Bridge_OIDC_Verifier $verifier)
    {
        $this->verifier = $verifier;
    }

    public function register(): void
    {
        add_action('rest_api_init', function (): void {
            register_rest_route('seo-workflow-bridge/v1', '/facebook/verify-publication', [
                'methods' => 'POST',
                'callback' => [$this, 'verify_publication'],
                'permission_callback' => '__return_true',
            ]);
        });
    }

    public function verify_publication(WP_REST_Request $request): WP_REST_Response
    {
        $bridge = get_option(self::BRIDGE_OPTION, []);
        $bridge = is_array($bridge) ? $bridge : [];
        if (empty($bridge['enabled'])) {
            return $this->error('bridge_disabled', 'SEO Workflow Bridge is disabled.', 503);
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

        $settings = get_option(self::FACEBOOK_SETTINGS_OPTION, []);
        $settings = is_array($settings) ? $settings : [];
        if (empty($settings['enabled'])) {
            return $this->error('facebook_page_disabled', 'Facebook Page publication capability is disabled.', 503);
        }

        $identity = get_option(self::FACEBOOK_IDENTITY_OPTION, []);
        $identity = is_array($identity) ? $identity : [];
        $configured_page_id = trim((string)($settings['page_id'] ?? ''));
        $verified_page_id = trim((string)($identity['page_id'] ?? ''));
        $page_access_token = trim((string)($settings['page_access_token'] ?? ''));
        $payload = $body['payload'];
        $page_id = (string)$payload['page_id'];

        if ($configured_page_id === '' || $verified_page_id === '' || $page_access_token === '') {
            return $this->error('facebook_page_connection_invalid', 'Facebook Page ID, token or verified identity is missing.', 409);
        }
        if (!hash_equals($configured_page_id, $verified_page_id) || !hash_equals($configured_page_id, $page_id)) {
            return $this->error('facebook_page_identity_drift', 'The verification target no longer matches the configured verified Page.', 409);
        }

        $post_id = (string)$payload['post_id'];
        $authorization_id = (string)$payload['authorization_id'];
        $remote_post_id = (string)$payload['remote_post_id'];
        $remote_media_id = (string)$payload['remote_media_id'];
        if (strpos($remote_post_id, $page_id . '_') !== 0) {
            return $this->error('facebook_page_remote_post_target_mismatch', 'The remote post ID is not bound to the expected Page ID.', 409);
        }

        // Read-back is allowed only for a publication result that this Bridge has
        // already persisted as definitive success. This prevents the verifier from
        // becoming a generic Page-object reader merely because a caller has valid
        // workflow OIDC credentials.
        $results = get_option(self::RESULT_OPTION, []);
        $results = is_array($results) ? $results : [];
        $evidence = isset($results[$post_id]) && is_array($results[$post_id]) ? $results[$post_id] : [];
        if (empty($evidence['published']) || (string)($evidence['publication_state'] ?? '') !== 'published') {
            return $this->error('facebook_page_verification_evidence_missing', 'No definitive Bridge publication evidence exists for this post.', 409);
        }
        $bindings = [
            'authorization_id' => $authorization_id,
            'page_id' => $page_id,
            'remote_post_id' => $remote_post_id,
            'remote_media_id' => $remote_media_id,
        ];
        foreach ($bindings as $key => $expected) {
            $actual = (string)($evidence[$key] ?? '');
            if ($actual === '' || !hash_equals($expected, $actual)) {
                return $this->error('facebook_page_verification_evidence_drift', 'Verification request no longer matches persisted Bridge publication evidence.', 409);
            }
        }

        $text = (string)$payload['text'];
        $text_sha256 = (string)$payload['text_sha256'];
        if (!hash_equals($text_sha256, hash('sha256', $text))) {
            return $this->error('facebook_page_verification_text_drift', 'Verification text hash does not match the expected text.', 409);
        }
        if (!hash_equals($text_sha256, (string)($evidence['text_sha256'] ?? ''))) {
            return $this->error('facebook_page_verification_evidence_drift', 'Verification text hash no longer matches persisted Bridge publication evidence.', 409);
        }

        $post = $this->graph_get(
            $remote_post_id,
            $page_access_token,
            'id,message,created_time,permalink_url'
        );
        if (is_wp_error($post)) {
            return $this->error($post->get_error_code(), $post->get_error_message(), 409);
        }
        if (!hash_equals($remote_post_id, (string)($post['id'] ?? ''))) {
            return $this->error('facebook_page_remote_post_id_mismatch', 'Meta returned a different remote post ID during verification.', 409);
        }
        $remote_message = (string)($post['message'] ?? '');
        if (!hash_equals($text_sha256, hash('sha256', $remote_message))) {
            return $this->error('facebook_page_remote_message_mismatch', 'Published Facebook message does not match the authorized text.', 409);
        }

        $media = $this->graph_get($remote_media_id, $page_access_token, 'id');
        if (is_wp_error($media)) {
            return $this->error($media->get_error_code(), $media->get_error_message(), 409);
        }
        if (!hash_equals($remote_media_id, (string)($media['id'] ?? ''))) {
            return $this->error('facebook_page_remote_media_id_mismatch', 'Meta returned a different remote media ID during verification.', 409);
        }

        $result = [
            'verified' => true,
            'verification_state' => 'remote_verified',
            'platform' => 'facebook',
            'target_type' => 'facebook_page',
            'post_id' => $post_id,
            'authorization_id' => $authorization_id,
            'page_id' => $page_id,
            'remote_post_id' => $remote_post_id,
            'remote_media_id' => $remote_media_id,
            'checked_at' => time(),
            'provider_http_status' => 200,
            'message_matches' => true,
            'media_exists' => true,
            'created_time' => isset($post['created_time']) ? (string)$post['created_time'] : null,
            'permalink_url' => isset($post['permalink_url']) ? esc_url_raw((string)$post['permalink_url']) : null,
            'github_run_id' => (string)($claims['run_id'] ?? ''),
        ];

        return new WP_REST_Response([
            'ok' => true,
            'schema_version' => 1,
            'request_id' => (string)$body['request_id'],
            'operation' => 'facebook_page_verify_publication',
            'result' => $result,
        ], 200);
    }

    /** @return true|WP_Error */
    private function validate_request(array $body)
    {
        if ((int)($body['schema_version'] ?? 0) !== 1) {
            return new WP_Error('unsupported_schema', 'Unsupported verification request schema_version.');
        }
        if ((string)($body['operation'] ?? '') !== 'facebook_page_verify_publication') {
            return new WP_Error('invalid_operation', 'Expected facebook_page_verify_publication operation.');
        }
        if (!preg_match('/^[A-Za-z0-9._:-]{8,128}$/', (string)($body['request_id'] ?? ''))) {
            return new WP_Error('invalid_request_id', 'Invalid verification request_id.');
        }
        $issued_at = strtotime((string)($body['issued_at'] ?? ''));
        if ($issued_at === false || abs(time() - $issued_at) > HOUR_IN_SECONDS) {
            return new WP_Error('stale_request', 'Verification request issued_at must be within one hour of server time.');
        }
        if (!is_array($body['payload'] ?? null)) {
            return new WP_Error('invalid_payload', 'Verification payload is required.');
        }
        $required = [
            'post_id', 'authorization_id', 'page_id', 'remote_post_id', 'remote_media_id', 'text', 'text_sha256',
        ];
        foreach ($required as $key) {
            if (!isset($body['payload'][$key]) || !is_string($body['payload'][$key]) || trim($body['payload'][$key]) === '') {
                return new WP_Error('facebook_page_verification_payload_incomplete', 'Missing verification field: ' . $key);
            }
        }
        if (!preg_match('/^[A-Za-z0-9._:-]{4,128}$/', (string)$body['payload']['post_id'])) {
            return new WP_Error('invalid_post_id', 'Facebook verification post_id has an unexpected format.');
        }
        if (!preg_match('/^[A-Za-z0-9._:-]{8,160}$/', (string)$body['payload']['authorization_id'])) {
            return new WP_Error('invalid_authorization_id', 'Facebook verification authorization_id has an unexpected format.');
        }
        if (!preg_match('/^[0-9]{5,32}$/', (string)$body['payload']['page_id'])) {
            return new WP_Error('invalid_page_id', 'Facebook Page ID must be numeric.');
        }
        if (!preg_match('/^[0-9]{5,32}_[0-9]{5,32}$/', (string)$body['payload']['remote_post_id'])) {
            return new WP_Error('invalid_remote_post_id', 'Facebook remote post ID has an unexpected format.');
        }
        if (!preg_match('/^[0-9]{5,32}$/', (string)$body['payload']['remote_media_id'])) {
            return new WP_Error('invalid_remote_media_id', 'Facebook remote media ID must be numeric.');
        }
        if (!preg_match('/^[a-f0-9]{64}$/', (string)$body['payload']['text_sha256'])) {
            return new WP_Error('invalid_text_sha256', 'text_sha256 must be lowercase hexadecimal SHA-256.');
        }
        return true;
    }

    /** @return array<string,mixed>|WP_Error */
    private function graph_get(string $object_id, string $token, string $fields)
    {
        $url = 'https://graph.facebook.com/' . self::GRAPH_API_VERSION . '/' . rawurlencode($object_id)
            . '?fields=' . rawurlencode($fields);
        $response = wp_remote_get($url, [
            'timeout' => 20,
            'headers' => [
                'Authorization' => 'Bearer ' . $token,
                'Accept' => 'application/json',
            ],
        ]);
        if (is_wp_error($response)) {
            return new WP_Error('facebook_page_remote_verification_transport', 'Unable to read the published Facebook object from Meta.');
        }
        $status = (int)wp_remote_retrieve_response_code($response);
        $body = json_decode((string)wp_remote_retrieve_body($response), true);
        if ($status !== 200 || !is_array($body) || isset($body['error'])) {
            return new WP_Error('facebook_page_remote_not_visible_yet', 'Meta did not return the published object during read-back verification.');
        }
        return $body;
    }

    private function error(string $code, string $message, int $status): WP_REST_Response
    {
        return new WP_REST_Response([
            'ok' => false,
            'error' => [
                'code' => $code,
                'message' => $message,
            ],
        ], $status);
    }
}
