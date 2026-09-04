<?php

declare(strict_types=1);

if (!defined('ABSPATH')) {
    exit;
}

final class SEO_Workflow_Bridge_LinkedIn_Media_Probe
{
    private const TOKEN_OPTION = 'seo_workflow_bridge_linkedin_token';
    private const IDENTITY_OPTION = 'seo_workflow_bridge_linkedin_identity';
    private const PROBE_OPTION = 'seo_workflow_bridge_linkedin_media_probe';
    private const IMAGES_URL = 'https://api.linkedin.com/rest/images?action=initializeUpload';
    private const LINKEDIN_VERSION = '202608';

    public function register(): void
    {
        add_action('admin_post_seo_workflow_bridge_linkedin_media_probe', [$this, 'run']);
        add_action('admin_notices', [$this, 'render_panel']);
    }

    /** @return array<string,mixed> */
    public static function status(): array
    {
        $probe = get_option(self::PROBE_OPTION, []);
        $probe = is_array($probe) ? $probe : [];
        return [
            'verified' => !empty($probe['verified']),
            'verified_at' => !empty($probe['verified_at']) ? (int)$probe['verified_at'] : null,
            'linkedin_version' => self::LINKEDIN_VERSION,
            'image_urn' => !empty($probe['image_urn']) ? (string)$probe['image_urn'] : null,
        ];
    }

    public function render_panel(): void
    {
        if (!current_user_can('manage_options')) {
            return;
        }
        $page = sanitize_key((string)($_GET['page'] ?? ''));
        if ($page !== 'seo-workflow-bridge-linkedin') {
            return;
        }

        $connection = SEO_Workflow_Bridge_LinkedIn_Controller::status();
        if (empty($connection['connected']) || empty($connection['member_verified'])) {
            return;
        }
        $probe = self::status();
        ?>
        <div class="notice notice-info" style="padding:12px 16px;">
            <p><strong>LinkedIn publishing identity probe</strong></p>
            <?php if (!empty($probe['verified'])): ?>
                <p>Media initialization: verified. LinkedIn accepted the connected member as the owner of a non-public image upload slot. No post and no image were published.</p>
                <?php if (!empty($probe['verified_at'])): ?>
                    <p>Verified: <?php echo esc_html(wp_date('Y-m-d H:i:s T', (int)$probe['verified_at'])); ?></p>
                <?php endif; ?>
            <?php else: ?>
                <p>This check calls LinkedIn Images API <code>initializeUpload</code> using the connected member identity. It creates only a temporary upload slot; it uploads no file and creates no post.</p>
                <form method="post" action="<?php echo esc_url(admin_url('admin-post.php')); ?>">
                    <input type="hidden" name="action" value="seo_workflow_bridge_linkedin_media_probe">
                    <?php wp_nonce_field('seo_workflow_bridge_linkedin_media_probe'); ?>
                    <?php submit_button('Verify LinkedIn publishing identity - no post', 'secondary', 'submit', false); ?>
                </form>
            <?php endif; ?>
        </div>
        <?php
    }

    public function run(): void
    {
        if (!current_user_can('manage_options')) {
            wp_die('Unauthorized.', 403);
        }
        check_admin_referer('seo_workflow_bridge_linkedin_media_probe');

        $token = get_option(self::TOKEN_OPTION, []);
        $token = is_array($token) ? $token : [];
        $identity = get_option(self::IDENTITY_OPTION, []);
        $identity = is_array($identity) ? $identity : [];

        $access_token = (string)($token['access_token'] ?? '');
        $expires_at = (int)($token['expires_at'] ?? 0);
        $subject = trim((string)($identity['sub'] ?? ''));
        if ($access_token === '' || $expires_at <= time() || $subject === '') {
            $this->redirect_admin('linkedin_media_probe_prerequisites_missing');
        }

        $owner = 'urn:li:person:' . $subject;
        $response = wp_remote_post(self::IMAGES_URL, [
            'timeout' => 20,
            'redirection' => 0,
            'headers' => [
                'Accept' => 'application/json',
                'Authorization' => 'Bearer ' . $access_token,
                'Content-Type' => 'application/json',
                'Linkedin-Version' => self::LINKEDIN_VERSION,
                'X-Restli-Protocol-Version' => '2.0.0',
            ],
            'body' => wp_json_encode([
                'initializeUploadRequest' => [
                    'owner' => $owner,
                ],
            ]),
        ]);

        if (is_wp_error($response)) {
            delete_option(self::PROBE_OPTION);
            $this->redirect_admin('linkedin_media_probe_failed');
        }

        $status = (int)wp_remote_retrieve_response_code($response);
        $body = json_decode((string)wp_remote_retrieve_body($response), true);
        $image_urn = is_array($body) ? sanitize_text_field((string)($body['value']['image'] ?? '')) : '';
        $upload_url = is_array($body) ? (string)($body['value']['uploadUrl'] ?? '') : '';

        if ($status < 200 || $status >= 300 || $image_urn === '' || $upload_url === '') {
            delete_option(self::PROBE_OPTION);
            $this->redirect_admin('linkedin_media_probe_failed');
        }

        update_option(self::PROBE_OPTION, [
            'verified' => true,
            'verified_at' => time(),
            'linkedin_version' => self::LINKEDIN_VERSION,
            'owner_urn' => $owner,
            'image_urn' => $image_urn,
        ], false);

        $this->redirect_admin('linkedin_media_probe_verified');
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
