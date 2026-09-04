<?php

declare(strict_types=1);

if (!defined('ABSPATH')) {
    exit;
}

final class SEO_Workflow_Bridge_Facebook_Page_Controller
{
    private const SETTINGS_OPTION = 'seo_workflow_bridge_facebook_page_settings';
    private const IDENTITY_OPTION = 'seo_workflow_bridge_facebook_page_identity';
    private const GRAPH_API_VERSION = 'v26.0';
    private const REQUIRED_PERMISSIONS = 'pages_show_list pages_read_engagement pages_manage_posts';

    public function register(): void
    {
        add_action('admin_post_seo_workflow_bridge_facebook_page_verify', [$this, 'verify']);
        add_action('admin_post_seo_workflow_bridge_facebook_page_disconnect', [$this, 'disconnect']);
    }

    /** @return array<string,mixed> */
    public static function status(): array
    {
        $settings = get_option(self::SETTINGS_OPTION, []);
        $settings = is_array($settings) ? $settings : [];
        $identity = get_option(self::IDENTITY_OPTION, []);
        $identity = is_array($identity) ? $identity : [];
        $page_id = trim((string)($settings['page_id'] ?? ''));
        $verified_page_id = trim((string)($identity['page_id'] ?? ''));

        return [
            'available' => true,
            'target_type' => 'facebook_page',
            'graph_api_version' => self::GRAPH_API_VERSION,
            'required_permissions' => self::REQUIRED_PERMISSIONS,
            'enabled' => !empty($settings['enabled']),
            'page_id_configured' => $page_id !== '',
            'page_id' => $page_id,
            'page_access_token_configured' => !empty($settings['page_access_token']),
            'page_verified' => $page_id !== '' && $verified_page_id !== '' && hash_equals($page_id, $verified_page_id),
            'page_name' => (string)($identity['page_name'] ?? ''),
            'verified_at' => (int)($identity['verified_at'] ?? 0),
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
        $settings = get_option(self::SETTINGS_OPTION, []);
        $settings = is_array($settings) ? $settings : [];
        $identity = get_option(self::IDENTITY_OPTION, []);
        $identity = is_array($identity) ? $identity : [];
        $page_id = trim((string)($settings['page_id'] ?? ''));
        $token = trim((string)($settings['page_access_token'] ?? ''));
        $verified_page_id = trim((string)($identity['page_id'] ?? ''));

        $health = $status;
        $health['credential_live_valid'] = false;
        $health['identity_matches'] = false;
        $health['provider_http_status'] = null;
        $health['renewal_mode'] = 'page_token_reprovision';

        if (empty($status['enabled']) || $page_id === '' || $token === '' || $verified_page_id === '') {
            return $health;
        }

        $result = self::fetch_page_identity($page_id, $token);
        if (is_wp_error($result)) {
            $data = $result->get_error_data();
            if (is_array($data) && isset($data['http_status'])) {
                $health['provider_http_status'] = (int)$data['http_status'];
            }
            return $health;
        }

        $matches = hash_equals($page_id, (string)$result['id']) && hash_equals($verified_page_id, (string)$result['id']);
        $health['provider_http_status'] = 200;
        $health['identity_matches'] = $matches;
        $health['credential_live_valid'] = $matches;
        $health['provider_page_name'] = (string)$result['name'];
        return $health;
    }

    public function verify(): void
    {
        if (!current_user_can('manage_options')) {
            wp_die('Unauthorized.', 403);
        }
        check_admin_referer('seo_workflow_bridge_facebook_page_verify');

        $settings = get_option(self::SETTINGS_OPTION, []);
        $settings = is_array($settings) ? $settings : [];
        if (empty($settings['enabled'])) {
            $this->redirect('facebook_page_disabled');
        }
        $page_id = trim((string)($settings['page_id'] ?? ''));
        $token = trim((string)($settings['page_access_token'] ?? ''));
        if (!preg_match('/^[0-9]{5,32}$/', $page_id) || $token === '') {
            $this->redirect('facebook_page_credentials_missing');
        }

        $result = self::fetch_page_identity($page_id, $token);
        if (is_wp_error($result)) {
            delete_option(self::IDENTITY_OPTION);
            $this->redirect('facebook_page_verification_failed');
        }
        if (!hash_equals($page_id, (string)$result['id'])) {
            delete_option(self::IDENTITY_OPTION);
            $this->redirect('facebook_page_identity_mismatch');
        }

        update_option(self::IDENTITY_OPTION, [
            'page_id' => (string)$result['id'],
            'page_name' => (string)$result['name'],
            'verified_at' => time(),
        ], false);
        $this->redirect('facebook_page_verified');
    }

    public function disconnect(): void
    {
        if (!current_user_can('manage_options')) {
            wp_die('Unauthorized.', 403);
        }
        check_admin_referer('seo_workflow_bridge_facebook_page_disconnect');
        $settings = get_option(self::SETTINGS_OPTION, []);
        $settings = is_array($settings) ? $settings : [];
        $settings['page_access_token'] = '';
        update_option(self::SETTINGS_OPTION, $settings, false);
        delete_option(self::IDENTITY_OPTION);
        $this->redirect('facebook_page_disconnected');
    }

    /** @return array<string,string>|WP_Error */
    private static function fetch_page_identity(string $page_id, string $token)
    {
        $url = 'https://graph.facebook.com/' . self::GRAPH_API_VERSION . '/' . rawurlencode($page_id) . '?fields=id,name';
        $response = wp_remote_get($url, [
            'timeout' => 20,
            'redirection' => 0,
            'headers' => [
                'Accept' => 'application/json',
                'Authorization' => 'Bearer ' . $token,
            ],
            'user-agent' => 'SEO-Workflow-Bridge/' . SEO_WORKFLOW_BRIDGE_VERSION,
        ]);
        if (is_wp_error($response)) {
            return new WP_Error('facebook_page_verify_request_failed', 'Unable to verify the Facebook Page token.');
        }
        $status = (int)wp_remote_retrieve_response_code($response);
        $body = json_decode((string)wp_remote_retrieve_body($response), true);
        if ($status !== 200 || !is_array($body)) {
            return new WP_Error(
                'facebook_page_verify_failed',
                'Meta did not return a valid Facebook Page identity.',
                ['http_status' => $status]
            );
        }
        $id = sanitize_text_field((string)($body['id'] ?? ''));
        $name = sanitize_text_field((string)($body['name'] ?? ''));
        if ($id === '' || $name === '') {
            return new WP_Error('facebook_page_verify_invalid', 'Meta Page identity is incomplete.');
        }
        return ['id' => $id, 'name' => $name];
    }

    private function redirect(string $notice): void
    {
        $url = add_query_arg([
            'page' => 'seo-workflow-bridge-facebook-page',
            'seo_workflow_bridge_notice' => $notice,
        ], admin_url('options-general.php'));
        wp_safe_redirect($url);
        exit;
    }
}
