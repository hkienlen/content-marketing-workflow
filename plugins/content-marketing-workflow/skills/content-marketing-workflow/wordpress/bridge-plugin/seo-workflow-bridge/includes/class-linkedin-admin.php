<?php

declare(strict_types=1);

if (!defined('ABSPATH')) {
    exit;
}

final class SEO_Workflow_Bridge_LinkedIn_Admin
{
    private const OPTION = 'seo_workflow_bridge_linkedin_settings';

    public function register(): void
    {
        add_action('admin_menu', [$this, 'menu']);
        add_action('admin_post_seo_workflow_bridge_linkedin_save', [$this, 'save']);
    }

    public function menu(): void
    {
        add_options_page(
            'SEO Workflow Bridge - LinkedIn',
            'SEO Workflow Bridge - LinkedIn',
            'manage_options',
            'seo-workflow-bridge-linkedin',
            [$this, 'render']
        );
    }

    public function save(): void
    {
        if (!current_user_can('manage_options')) {
            wp_die('Unauthorized.', 403);
        }
        check_admin_referer('seo_workflow_bridge_linkedin_save');

        $current = get_option(self::OPTION, []);
        $current = is_array($current) ? $current : [];
        $raw = isset($_POST['linkedin']) && is_array($_POST['linkedin']) ? wp_unslash($_POST['linkedin']) : [];

        $client_id = sanitize_text_field((string)($raw['client_id'] ?? ''));
        $incoming_secret = trim((string)($raw['client_secret'] ?? ''));
        $secret = $incoming_secret !== '' ? $incoming_secret : (string)($current['client_secret'] ?? '');

        $settings = [
            'enabled' => !empty($raw['enabled']),
            'client_id' => $client_id,
            'client_secret' => $secret,
        ];
        update_option(self::OPTION, $settings, false);

        $url = add_query_arg([
            'page' => 'seo-workflow-bridge-linkedin',
            'seo_workflow_bridge_notice' => 'linkedin_settings_saved',
        ], admin_url('options-general.php'));
        wp_safe_redirect($url);
        exit;
    }

    public function render(): void
    {
        if (!current_user_can('manage_options')) {
            return;
        }
        $settings = get_option(self::OPTION, []);
        $settings = is_array($settings) ? $settings : [];
        $status = SEO_Workflow_Bridge_LinkedIn_Controller::status();
        $notice = sanitize_key((string)($_GET['seo_workflow_bridge_notice'] ?? ''));
        ?>
        <div class="wrap">
            <h1>SEO Workflow Bridge - LinkedIn</h1>
            <p>Connects a LinkedIn member account for direct publication through the Bridge. Connection does not authorize publishing any specific post.</p>
            <?php if ($notice !== ''): ?>
                <div class="notice notice-info"><p><?php echo esc_html($this->notice_text($notice)); ?></p></div>
            <?php endif; ?>

            <h2>OAuth callback URL</h2>
            <p>Register this exact URL under LinkedIn Developer Portal → Auth → Authorized redirect URLs for your app:</p>
            <p><code><?php echo esc_html((string)$status['callback_url']); ?></code></p>

            <form method="post" action="<?php echo esc_url(admin_url('admin-post.php')); ?>">
                <input type="hidden" name="action" value="seo_workflow_bridge_linkedin_save">
                <?php wp_nonce_field('seo_workflow_bridge_linkedin_save'); ?>
                <table class="form-table" role="presentation">
                    <tr>
                        <th scope="row">LinkedIn publication capability</th>
                        <td><label><input type="checkbox" name="linkedin[enabled]" value="1" <?php checked(!empty($settings['enabled'])); ?>> Enable LinkedIn OAuth connection support.</label><p class="description">This does not authorize publication. Exact post publication remains separately gated.</p></td>
                    </tr>
                    <tr>
                        <th scope="row">Client ID</th>
                        <td><input class="regular-text code" name="linkedin[client_id]" value="<?php echo esc_attr((string)($settings['client_id'] ?? '')); ?>" autocomplete="off"></td>
                    </tr>
                    <tr>
                        <th scope="row">Client Secret</th>
                        <td><input class="regular-text code" type="password" name="linkedin[client_secret]" value="" autocomplete="new-password" placeholder="<?php echo !empty($settings['client_secret']) ? esc_attr('Stored - leave blank to keep') : esc_attr('Enter Client Secret'); ?>"><p class="description">The stored secret is never displayed again. Do not paste it into chat or GitHub.</p></td>
                    </tr>
                </table>
                <?php submit_button('Save LinkedIn settings'); ?>
            </form>

            <h2>Connection status</h2>
            <p><strong>Required scopes:</strong> <code><?php echo esc_html((string)$status['required_scopes']); ?></code></p>
            <p><strong>Credentials:</strong> <?php echo (!empty($status['client_id_configured']) && !empty($status['client_secret_configured'])) ? 'configured' : 'incomplete'; ?></p>
            <p><strong>OAuth:</strong> <?php echo !empty($status['connected']) ? 'connected' : 'not connected'; ?></p>
            <p><strong>Member:</strong> <?php echo !empty($status['member_verified']) ? 'verified' : 'not verified'; ?></p>
            <?php if (!empty($status['member_verified']) && !empty($status['member_name'])): ?>
                <p><strong>Connected member:</strong> <?php echo esc_html((string)$status['member_name']); ?></p>
            <?php endif; ?>
            <?php if (!empty($status['connected']) && !empty($status['expires_at'])): ?>
                <p><strong>Token expiry:</strong> <?php echo esc_html(wp_date('Y-m-d H:i:s T', (int)$status['expires_at'])); ?></p>
            <?php endif; ?>

            <?php if (!empty($settings['enabled']) && !empty($status['client_id_configured']) && !empty($status['client_secret_configured']) && (empty($status['connected']) || empty($status['member_verified']))): ?>
                <form method="post" action="<?php echo esc_url(admin_url('admin-post.php')); ?>">
                    <input type="hidden" name="action" value="seo_workflow_bridge_linkedin_connect">
                    <?php wp_nonce_field('seo_workflow_bridge_linkedin_connect'); ?>
                    <?php submit_button(!empty($status['connected']) ? 'Reconnect LinkedIn to verify member' : 'Connect LinkedIn', 'primary'); ?>
                </form>
            <?php endif; ?>

            <?php if (!empty($status['connected'])): ?>
                <form method="post" action="<?php echo esc_url(admin_url('admin-post.php')); ?>">
                    <input type="hidden" name="action" value="seo_workflow_bridge_linkedin_disconnect">
                    <?php wp_nonce_field('seo_workflow_bridge_linkedin_disconnect'); ?>
                    <?php submit_button('Disconnect LinkedIn', 'secondary'); ?>
                </form>
            <?php endif; ?>
        </div>
        <?php
    }

    private function notice_text(string $notice): string
    {
        $messages = [
            'linkedin_settings_saved' => 'LinkedIn settings saved.',
            'linkedin_connected' => 'LinkedIn OAuth connection completed. No post has been published.',
            'linkedin_connected_verified' => 'LinkedIn OAuth connection and member verification completed. No post has been published.',
            'linkedin_disconnected' => 'LinkedIn connection removed.',
            'linkedin_disabled' => 'Enable the LinkedIn capability before connecting.',
            'linkedin_credentials_missing' => 'Client ID and Client Secret are required.',
            'linkedin_https_required' => 'The WordPress REST callback must use HTTPS.',
            'linkedin_oauth_denied' => 'LinkedIn authorization was cancelled or denied.',
            'linkedin_oauth_missing_parameters' => 'LinkedIn callback parameters are incomplete.',
            'linkedin_oauth_state_invalid' => 'OAuth state is invalid or already used. Start the connection again.',
            'linkedin_oauth_state_expired' => 'OAuth state expired. Start the connection again.',
            'linkedin_token_exchange_failed' => 'LinkedIn token exchange failed. No token was stored.',
            'linkedin_token_invalid' => 'LinkedIn returned an invalid token response. No token was stored.',
            'linkedin_identity_verification_failed' => 'LinkedIn OAuth completed but member identity could not be verified. Ensure Sign in with LinkedIn using OpenID Connect is enabled, then reconnect.',
        ];
        return $messages[$notice] ?? 'LinkedIn connection status updated.';
    }
}
