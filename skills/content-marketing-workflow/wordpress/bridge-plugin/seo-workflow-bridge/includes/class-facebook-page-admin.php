<?php

declare(strict_types=1);

if (!defined('ABSPATH')) {
    exit;
}

final class SEO_Workflow_Bridge_Facebook_Page_Admin
{
    private const OPTION = 'seo_workflow_bridge_facebook_page_settings';
    private const IDENTITY_OPTION = 'seo_workflow_bridge_facebook_page_identity';

    public function register(): void
    {
        add_action('admin_menu', [$this, 'menu']);
        add_action('admin_post_seo_workflow_bridge_facebook_page_save', [$this, 'save']);
    }

    public function menu(): void
    {
        add_options_page(
            'SEO Workflow Bridge - Facebook Page',
            'SEO Workflow Bridge - Facebook Page',
            'manage_options',
            'seo-workflow-bridge-facebook-page',
            [$this, 'render']
        );
    }

    public function save(): void
    {
        if (!current_user_can('manage_options')) {
            wp_die('Unauthorized.', 403);
        }
        check_admin_referer('seo_workflow_bridge_facebook_page_save');

        $current = get_option(self::OPTION, []);
        $current = is_array($current) ? $current : [];
        $raw = isset($_POST['facebook_page']) && is_array($_POST['facebook_page']) ? wp_unslash($_POST['facebook_page']) : [];

        $page_id = preg_replace('/\D+/', '', (string)($raw['page_id'] ?? ''));
        $incoming_token = trim((string)($raw['page_access_token'] ?? ''));
        $token = $incoming_token !== '' ? $incoming_token : (string)($current['page_access_token'] ?? '');
        $changed = $page_id !== (string)($current['page_id'] ?? '') || $incoming_token !== '';

        update_option(self::OPTION, [
            'enabled' => !empty($raw['enabled']),
            'page_id' => $page_id,
            'page_access_token' => $token,
        ], false);
        if ($changed) {
            delete_option(self::IDENTITY_OPTION);
        }

        $this->redirect('facebook_page_settings_saved');
    }

    public function render(): void
    {
        if (!current_user_can('manage_options')) {
            return;
        }
        $settings = get_option(self::OPTION, []);
        $settings = is_array($settings) ? $settings : [];
        $status = SEO_Workflow_Bridge_Facebook_Page_Controller::status();
        $notice = sanitize_key((string)($_GET['seo_workflow_bridge_notice'] ?? ''));
        ?>
        <div class="wrap">
            <h1>SEO Workflow Bridge - Facebook Page</h1>
            <p>Connects one exact Facebook Page for Page-only API publication. Personal/professional Facebook profiles are not publication targets.</p>
            <p><strong>Important:</strong> configuring or verifying the Page never authorizes publication of any post. Every unattended publication remains separately authorized per exact post revision and time.</p>
            <?php if ($notice !== ''): ?>
                <div class="notice notice-info"><p><?php echo esc_html($this->notice_text($notice)); ?></p></div>
            <?php endif; ?>

            <form method="post" action="<?php echo esc_url(admin_url('admin-post.php')); ?>">
                <input type="hidden" name="action" value="seo_workflow_bridge_facebook_page_save">
                <?php wp_nonce_field('seo_workflow_bridge_facebook_page_save'); ?>
                <table class="form-table" role="presentation">
                    <tr>
                        <th scope="row">Facebook Page publication capability</th>
                        <td><label><input type="checkbox" name="facebook_page[enabled]" value="1" <?php checked(!empty($settings['enabled'])); ?>> Enable Facebook Page connection support.</label></td>
                    </tr>
                    <tr>
                        <th scope="row">Page ID</th>
                        <td><input class="regular-text code" inputmode="numeric" name="facebook_page[page_id]" value="<?php echo esc_attr((string)($settings['page_id'] ?? '')); ?>" autocomplete="off"><p class="description">Numeric ID of the exact Facebook Page to publish to.</p></td>
                    </tr>
                    <tr>
                        <th scope="row">Page Access Token</th>
                        <td><input class="large-text code" type="password" name="facebook_page[page_access_token]" value="" autocomplete="new-password" placeholder="<?php echo !empty($settings['page_access_token']) ? esc_attr('Stored - leave blank to keep') : esc_attr('Enter Page Access Token'); ?>"><p class="description">Stored only in WordPress and never displayed again. Do not paste this token into chat or GitHub.</p></td>
                    </tr>
                </table>
                <?php submit_button('Save Facebook Page settings'); ?>
            </form>

            <h2>Connection requirements</h2>
            <p><strong>Target type:</strong> <code>facebook_page</code></p>
            <p><strong>Graph API:</strong> <code><?php echo esc_html((string)$status['graph_api_version']); ?></code></p>
            <p><strong>Required onboarding permissions:</strong> <code><?php echo esc_html((string)$status['required_permissions']); ?></code></p>
            <p>The Meta user granting the Page token must have sufficient Page task access to create content. The Bridge verifies the exact Page identity; a real post is still never created during connection verification.</p>

            <h2>Connection status</h2>
            <p><strong>Credentials:</strong> <?php echo (!empty($status['page_id_configured']) && !empty($status['page_access_token_configured'])) ? 'configured' : 'incomplete'; ?></p>
            <p><strong>Page:</strong> <?php echo !empty($status['page_verified']) ? 'verified' : 'not verified'; ?></p>
            <?php if (!empty($status['page_verified'])): ?>
                <p><strong>Verified Page ID:</strong> <code><?php echo esc_html((string)$status['page_id']); ?></code></p>
                <p><strong>Verified Page name:</strong> <?php echo esc_html((string)$status['page_name']); ?></p>
                <?php if (!empty($status['verified_at'])): ?>
                    <p><strong>Verified at:</strong> <?php echo esc_html(wp_date('Y-m-d H:i:s T', (int)$status['verified_at'])); ?></p>
                <?php endif; ?>
            <?php endif; ?>

            <?php if (!empty($settings['enabled']) && !empty($status['page_id_configured']) && !empty($status['page_access_token_configured'])): ?>
                <form method="post" action="<?php echo esc_url(admin_url('admin-post.php')); ?>">
                    <input type="hidden" name="action" value="seo_workflow_bridge_facebook_page_verify">
                    <?php wp_nonce_field('seo_workflow_bridge_facebook_page_verify'); ?>
                    <?php submit_button(!empty($status['page_verified']) ? 'Re-verify Facebook Page' : 'Verify Facebook Page', 'primary'); ?>
                </form>
            <?php endif; ?>

            <?php if (!empty($status['page_access_token_configured'])): ?>
                <form method="post" action="<?php echo esc_url(admin_url('admin-post.php')); ?>">
                    <input type="hidden" name="action" value="seo_workflow_bridge_facebook_page_disconnect">
                    <?php wp_nonce_field('seo_workflow_bridge_facebook_page_disconnect'); ?>
                    <?php submit_button('Remove Facebook Page token', 'secondary'); ?>
                </form>
            <?php endif; ?>
        </div>
        <?php
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

    private function notice_text(string $notice): string
    {
        $messages = [
            'facebook_page_settings_saved' => 'Facebook Page settings saved. No post has been published.',
            'facebook_page_verified' => 'Facebook Page identity verified. No post has been published.',
            'facebook_page_disconnected' => 'Facebook Page token removed.',
            'facebook_page_disabled' => 'Enable the Facebook Page capability before verification.',
            'facebook_page_credentials_missing' => 'Page ID and Page Access Token are required.',
            'facebook_page_verification_failed' => 'Meta could not verify this Page/token combination. Check the Page ID, token and required permissions.',
            'facebook_page_identity_mismatch' => 'Meta returned a different Page identity; verification was rejected.',
        ];
        return $messages[$notice] ?? 'Facebook Page connection status updated.';
    }
}
