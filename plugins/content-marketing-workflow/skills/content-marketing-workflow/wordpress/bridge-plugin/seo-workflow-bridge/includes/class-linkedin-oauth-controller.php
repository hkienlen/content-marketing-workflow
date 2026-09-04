<?php

declare(strict_types=1);

if (!defined('ABSPATH')) {
    exit;
}

final class SEO_Workflow_Bridge_LinkedIn_Controller
{
    private const SETTINGS_OPTION = 'seo_workflow_bridge_linkedin_settings';
    private const TOKEN_OPTION = 'seo_workflow_bridge_linkedin_token';
    private const IDENTITY_OPTION = 'seo_workflow_bridge_linkedin_identity';
    private const STATE_PREFIX = 'seo_workflow_bridge_linkedin_state_';
    private const REQUIRED_SCOPES = 'openid profile w_member_social';
    private const AUTH_URL = 'https://www.linkedin.com/oauth/v2/authorization';
    private const TOKEN_URL = 'https://www.linkedin.com/oauth/v2/accessToken';
    private const USERINFO_URL = 'https://api.linkedin.com/v2/userinfo';

    public function register(): void
    {
        add_action('rest_api_init', [$this, 'register_routes']);
        add_action('admin_post_seo_workflow_bridge_linkedin_connect', [$this, 'start_connection']);
        add_action('admin_post_seo_workflow_bridge_linkedin_disconnect', [$this, 'disconnect']);
    }

    public function register_routes(): void
    {
        register_rest_route('seo-workflow-bridge/v1', '/linkedin/oauth/callback', [
            'methods' => 'GET',
            'callback' => [$this, 'oauth_callback'],
            'permission_callback' => '__return_true',
        ]);
    }

    public static function callback_url(): string
    {
        return rest_url('seo-workflow-bridge/v1/linkedin/oauth/callback');
    }

    /** @return array<string,mixed> */
    public static function status(): array
    {
        $settings = get_option(self::SETTINGS_OPTION, []);
        $settings = is_array($settings) ? $settings : [];
        $token = get_option(self::TOKEN_OPTION, []);
        $token = is_array($token) ? $token : [];
        $identity = get_option(self::IDENTITY_OPTION, []);
        $identity = is_array($identity) ? $identity : [];
        $access_token_present = !empty($token['access_token']);
        $expires_at = (int)($token['expires_at'] ?? 0);
        $connected = $access_token_present && $expires_at > time();
        $identity_present = !empty($identity['sub']);
        $member_verified = $connected && $identity_present;

        return [
            'available' => true,
            'enabled' => !empty($settings['enabled']),
            'client_id_configured' => !empty($settings['client_id']),
            'client_secret_configured' => !empty($settings['client_secret']),
            'token_present' => $access_token_present,
            'connected' => $connected,
            'token_state' => !$access_token_present ? 'missing' : ($connected ? 'valid_by_time' : 'expired_by_time'),
            'member_verified' => $member_verified,
            'member_subject' => $identity_present ? (string)$identity['sub'] : null,
            'member_name' => $identity_present ? (string)($identity['name'] ?? '') : null,
            'expires_at' => $expires_at > 0 ? $expires_at : null,
            'required_scopes' => self::REQUIRED_SCOPES,
            'provider_scope' => $access_token_present ? (string)($token['provider_scope'] ?? '') : '',
            'callback_url' => self::callback_url(),
        ];
    }

    /**
     * Provider-active read-only credential/identity probe.
     *
     * @return array<string,mixed>
     */
    public static function health_status(): array
    {
        $status = self::status();
        $token = get_option(self::TOKEN_OPTION, []);
        $token = is_array($token) ? $token : [];
        $identity = get_option(self::IDENTITY_OPTION, []);
        $identity = is_array($identity) ? $identity : [];
        $access_token = trim((string)($token['access_token'] ?? ''));
        $expected_subject = trim((string)($identity['sub'] ?? ''));
        $expires_at = (int)($token['expires_at'] ?? 0);

        $health = $status;
        $health['credential_live_valid'] = false;
        $health['identity_matches'] = false;
        $health['provider_http_status'] = null;
        $health['renewal_mode'] = 'oauth_reconnect';

        if (empty($status['enabled']) || $access_token === '' || $expected_subject === '' || $expires_at <= time()) {
            return $health;
        }

        $response = wp_remote_get(self::USERINFO_URL, [
            'timeout' => 20,
            'redirection' => 0,
            'headers' => [
                'Accept' => 'application/json',
                'Authorization' => 'Bearer ' . $access_token,
            ],
            'user-agent' => 'SEO-Workflow-Bridge/' . SEO_WORKFLOW_BRIDGE_VERSION,
        ]);
        if (is_wp_error($response)) {
            return $health;
        }

        $provider_status = (int)wp_remote_retrieve_response_code($response);
        $health['provider_http_status'] = $provider_status;
        $body = json_decode((string)wp_remote_retrieve_body($response), true);
        if ($provider_status < 200 || $provider_status >= 300 || !is_array($body)) {
            return $health;
        }

        $actual_subject = sanitize_text_field((string)($body['sub'] ?? ''));
        $matches = $actual_subject !== '' && hash_equals($expected_subject, $actual_subject);
        $health['identity_matches'] = $matches;
        $health['credential_live_valid'] = $matches;
        return $health;
    }

    public function start_connection(): void
    {
        if (!current_user_can('manage_options')) {
            wp_die('Unauthorized.', 403);
        }
        check_admin_referer('seo_workflow_bridge_linkedin_connect');

        $settings = get_option(self::SETTINGS_OPTION, []);
        $settings = is_array($settings) ? $settings : [];
        if (empty($settings['enabled'])) {
            $this->redirect_admin('linkedin_disabled');
        }
        $client_id = trim((string)($settings['client_id'] ?? ''));
        $client_secret = (string)($settings['client_secret'] ?? '');
        if ($client_id === '' || $client_secret === '') {
            $this->redirect_admin('linkedin_credentials_missing');
        }

        $redirect_uri = self::callback_url();
        if (stripos($redirect_uri, 'https://') !== 0) {
            $this->redirect_admin('linkedin_https_required');
        }

        $state = bin2hex(random_bytes(32));
        $key = self::STATE_PREFIX . hash('sha256', $state);
        set_transient($key, [
            'user_id' => get_current_user_id(),
            'created_at' => time(),
        ], 10 * MINUTE_IN_SECONDS);

        $url = add_query_arg([
            'response_type' => 'code',
            'client_id' => $client_id,
            'redirect_uri' => $redirect_uri,
            'state' => $state,
            'scope' => self::REQUIRED_SCOPES,
        ], self::AUTH_URL);

        wp_redirect($url, 302, 'SEO Workflow Bridge');
        exit;
    }

    public function oauth_callback(WP_REST_Request $request): WP_REST_Response
    {
        $error = sanitize_text_field((string)$request->get_param('error'));
        if ($error !== '') {
            return $this->callback_redirect('linkedin_oauth_denied');
        }

        $state = (string)$request->get_param('state');
        $code = (string)$request->get_param('code');
        if ($state === '' || $code === '') {
            return $this->callback_redirect('linkedin_oauth_missing_parameters');
        }

        $key = self::STATE_PREFIX . hash('sha256', $state);
        $state_payload = get_transient($key);
        delete_transient($key);
        if (!is_array($state_payload) || empty($state_payload['created_at'])) {
            return $this->callback_redirect('linkedin_oauth_state_invalid');
        }
        if ((int)$state_payload['created_at'] < time() - (10 * MINUTE_IN_SECONDS)) {
            return $this->callback_redirect('linkedin_oauth_state_expired');
        }

        $settings = get_option(self::SETTINGS_OPTION, []);
        $settings = is_array($settings) ? $settings : [];
        if (empty($settings['enabled'])) {
            return $this->callback_redirect('linkedin_disabled');
        }
        $client_id = trim((string)($settings['client_id'] ?? ''));
        $client_secret = (string)($settings['client_secret'] ?? '');
        if ($client_id === '' || $client_secret === '') {
            return $this->callback_redirect('linkedin_credentials_missing');
        }

        $response = wp_remote_post(self::TOKEN_URL, [
            'timeout' => 20,
            'redirection' => 0,
            'headers' => [
                'Accept' => 'application/json',
                'Content-Type' => 'application/x-www-form-urlencoded',
            ],
            'body' => [
                'grant_type' => 'authorization_code',
                'code' => $code,
                'client_id' => $client_id,
                'client_secret' => $client_secret,
                'redirect_uri' => self::callback_url(),
            ],
        ]);

        if (is_wp_error($response)) {
            return $this->callback_redirect('linkedin_token_exchange_failed');
        }
        $status = (int)wp_remote_retrieve_response_code($response);
        $body = json_decode((string)wp_remote_retrieve_body($response), true);
        if ($status < 200 || $status >= 300 || !is_array($body)) {
            return $this->callback_redirect('linkedin_token_exchange_failed');
        }

        $access_token = (string)($body['access_token'] ?? '');
        $expires_in = (int)($body['expires_in'] ?? 0);
        if ($access_token === '' || $expires_in <= 0) {
            return $this->callback_redirect('linkedin_token_invalid');
        }

        $identity_response = wp_remote_get(self::USERINFO_URL, [
            'timeout' => 20,
            'redirection' => 0,
            'headers' => [
                'Accept' => 'application/json',
                'Authorization' => 'Bearer ' . $access_token,
            ],
        ]);
        if (is_wp_error($identity_response)) {
            return $this->callback_redirect('linkedin_identity_verification_failed');
        }
        $identity_status = (int)wp_remote_retrieve_response_code($identity_response);
        $identity_body = json_decode((string)wp_remote_retrieve_body($identity_response), true);
        if ($identity_status < 200 || $identity_status >= 300 || !is_array($identity_body)) {
            return $this->callback_redirect('linkedin_identity_verification_failed');
        }

        $subject = sanitize_text_field((string)($identity_body['sub'] ?? ''));
        if ($subject === '') {
            return $this->callback_redirect('linkedin_identity_verification_failed');
        }

        $token = [
            'access_token' => $access_token,
            'expires_at' => time() + $expires_in,
            'obtained_at' => time(),
            'requested_scope' => self::REQUIRED_SCOPES,
        ];
        if (isset($body['scope']) && is_string($body['scope'])) {
            $token['provider_scope'] = sanitize_text_field($body['scope']);
        }
        update_option(self::TOKEN_OPTION, $token, false);

        update_option(self::IDENTITY_OPTION, [
            'sub' => $subject,
            'name' => sanitize_text_field((string)($identity_body['name'] ?? '')),
            'given_name' => sanitize_text_field((string)($identity_body['given_name'] ?? '')),
            'family_name' => sanitize_text_field((string)($identity_body['family_name'] ?? '')),
            'verified_at' => time(),
        ], false);

        return $this->callback_redirect('linkedin_connected_verified');
    }

    public function disconnect(): void
    {
        if (!current_user_can('manage_options')) {
            wp_die('Unauthorized.', 403);
        }
        check_admin_referer('seo_workflow_bridge_linkedin_disconnect');
        delete_option(self::TOKEN_OPTION);
        delete_option(self::IDENTITY_OPTION);
        $this->redirect_admin('linkedin_disconnected');
    }

    private function callback_redirect(string $notice): WP_REST_Response
    {
        $url = add_query_arg([
            'page' => 'seo-workflow-bridge-linkedin',
            'seo_workflow_bridge_notice' => $notice,
        ], admin_url('options-general.php'));
        $response = new WP_REST_Response(null, 302);
        $response->header('Location', $url);
        $response->header('Cache-Control', 'no-store');
        return $response;
    }

    private function redirect_admin(string $notice): void
    {
        $url = add_query_arg([
            'page' => 'seo-workflow-bridge-linkedin',
            'seo_workflow_bridge_notice' => $notice,
        ], admin_url('options-general.php'));
        wp_safe_redirect($url);
        exit;
    }
}
