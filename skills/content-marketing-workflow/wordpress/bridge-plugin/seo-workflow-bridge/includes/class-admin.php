<?php

declare(strict_types=1);

if (!defined('ABSPATH')) {
    exit;
}

final class SEO_Workflow_Bridge_Admin
{
    private const OPTION = 'seo_workflow_bridge_settings';

    public function register(): void
    {
        add_action('admin_menu', [$this, 'menu']);
        add_action('admin_init', [$this, 'settings']);
    }

    public function menu(): void
    {
        add_options_page(
            'SEO Workflow Bridge',
            'SEO Workflow Bridge',
            'manage_options',
            'seo-workflow-bridge',
            [$this, 'render']
        );
    }

    public function settings(): void
    {
        register_setting('seo_workflow_bridge', self::OPTION, [
            'type' => 'array',
            'sanitize_callback' => [$this, 'sanitize'],
            'default' => [],
        ]);
    }

    public function sanitize($raw): array
    {
        $raw = is_array($raw) ? $raw : [];
        return [
            'enabled' => !empty($raw['enabled']),
            'repository' => sanitize_text_field((string)($raw['repository'] ?? '')),
            'repository_id' => preg_replace('/\D+/', '', (string)($raw['repository_id'] ?? '')),
            'repository_owner_id' => preg_replace('/\D+/', '', (string)($raw['repository_owner_id'] ?? '')),
            'workflow_ref' => sanitize_text_field((string)($raw['workflow_ref'] ?? '')),
            'audience' => sanitize_text_field((string)($raw['audience'] ?? '')),
            'require_private_repository' => !empty($raw['require_private_repository']),
            'allow_content_read' => !empty($raw['allow_content_read']),
            'allow_connection_test_writes' => !empty($raw['allow_connection_test_writes']),
            'allow_article_prepare' => !empty($raw['allow_article_prepare']),
            'allow_article_publish' => !empty($raw['allow_article_publish']),
            'allowed_prepare_meta_keys' => $this->sanitize_csv((string)($raw['allowed_prepare_meta_keys'] ?? '')),
            'allowed_prepare_taxonomies' => $this->sanitize_csv((string)($raw['allowed_prepare_taxonomies'] ?? 'category,post_tag')),
        ];
    }

    private function sanitize_csv(string $value): string
    {
        $items = preg_split('/[,\r\n]+/', $value) ?: [];
        $clean = [];
        foreach ($items as $item) {
            $item = trim($item);
            if ($item === '' || !preg_match('/^[A-Za-z0-9_.:-]{1,128}$/', $item)) {
                continue;
            }
            $clean[$item] = true;
        }
        return implode(',', array_keys($clean));
    }

    public function render(): void
    {
        if (!current_user_can('manage_options')) {
            return;
        }
        $s = get_option(self::OPTION, []);
        $s = is_array($s) ? $s : [];
        $name = self::OPTION;
        ?>
        <div class="wrap">
            <h1>SEO Workflow Bridge</h1>
            <p>Authenticates a narrow GitHub Actions relay with short-lived GitHub OIDC tokens. No WordPress password or shared GitHub secret is required.</p>
            <form method="post" action="options.php">
                <?php settings_fields('seo_workflow_bridge'); ?>
                <table class="form-table" role="presentation">
                    <tr><th scope="row">Enable relay</th><td><label><input type="checkbox" name="<?php echo esc_attr($name); ?>[enabled]" value="1" <?php checked(!empty($s['enabled'])); ?>> Accept authenticated relay requests.</label></td></tr>
                    <tr><th scope="row">GitHub repository</th><td><input class="regular-text" name="<?php echo esc_attr($name); ?>[repository]" value="<?php echo esc_attr((string)($s['repository'] ?? '')); ?>" placeholder="owner/repository"></td></tr>
                    <tr><th scope="row">GitHub repository ID</th><td><input class="regular-text" inputmode="numeric" name="<?php echo esc_attr($name); ?>[repository_id]" value="<?php echo esc_attr((string)($s['repository_id'] ?? '')); ?>"><p class="description">Stable numeric repository ID. Required.</p></td></tr>
                    <tr><th scope="row">GitHub repository owner ID</th><td><input class="regular-text" inputmode="numeric" name="<?php echo esc_attr($name); ?>[repository_owner_id]" value="<?php echo esc_attr((string)($s['repository_owner_id'] ?? '')); ?>"></td></tr>
                    <tr><th scope="row">Allowed workflow ref</th><td><input class="large-text code" name="<?php echo esc_attr($name); ?>[workflow_ref]" value="<?php echo esc_attr((string)($s['workflow_ref'] ?? '')); ?>" placeholder="owner/repo/.github/workflows/wordpress-relay.yml@refs/heads/main"></td></tr>
                    <tr><th scope="row">OIDC audience</th><td><input class="regular-text code" name="<?php echo esc_attr($name); ?>[audience]" value="<?php echo esc_attr((string)($s['audience'] ?? '')); ?>" placeholder="wordpress-relay:site-primary"></td></tr>
                    <tr><th scope="row">Repository visibility</th><td><label><input type="checkbox" name="<?php echo esc_attr($name); ?>[require_private_repository]" value="1" <?php checked(!empty($s['require_private_repository'])); ?>> Require the OIDC token to report a private repository.</label></td></tr>
                    <tr><th scope="row">Read content</th><td><label><input type="checkbox" name="<?php echo esc_attr($name); ?>[allow_content_read]" value="1" <?php checked(!empty($s['allow_content_read'])); ?>> Allow site info and content-list/read operations.</label></td></tr>
                    <tr><th scope="row">Connection-test writes</th><td><label><input type="checkbox" name="<?php echo esc_attr($name); ?>[allow_connection_test_writes]" value="1" <?php checked(!empty($s['allow_connection_test_writes'])); ?>> Allow only temporary <code>AI connection test</code> draft create/read/delete operations.</label><p class="description">Keep disabled except during an explicitly approved connection test.</p></td></tr>
                    <tr><th scope="row">Article draft preparation</th><td><label><input type="checkbox" name="<?php echo esc_attr($name); ?>[allow_article_prepare]" value="1" <?php checked(!empty($s['allow_article_prepare'])); ?>> Allow repository-backed media upsert and create/update of bridge-managed WordPress drafts. This permission cannot publish posts.</label></td></tr>
                    <tr><th scope="row">Article publication</th><td><label><input type="checkbox" name="<?php echo esc_attr($name); ?>[allow_article_publish]" value="1" <?php checked(!empty($s['allow_article_publish'])); ?>> Allow only a validated bridge-managed draft to transition from <code>draft</code> to <code>publish</code>. This permission does not edit article content, media, taxonomies or metadata.</label><p class="description">Keep disabled until the user explicitly authorizes publication of a specific validated candidate. Disable it again after publication.</p></td></tr>
                    <tr><th scope="row">Allowed preparation meta keys</th><td><textarea class="large-text code" rows="4" name="<?php echo esc_attr($name); ?>[allowed_prepare_meta_keys]" placeholder="_example_meta_key,another_key"><?php echo esc_textarea((string)($s['allowed_prepare_meta_keys'] ?? '')); ?></textarea><p class="description">Comma- or line-separated allowlist. Article preparation rejects every post meta key not listed here. Publication may only verify keys from this same allowlist.</p></td></tr>
                    <tr><th scope="row">Allowed preparation taxonomies</th><td><input class="regular-text code" name="<?php echo esc_attr($name); ?>[allowed_prepare_taxonomies]" value="<?php echo esc_attr((string)($s['allowed_prepare_taxonomies'] ?? 'category,post_tag')); ?>"><p class="description">Comma-separated taxonomy allowlist used during draft preparation and publication drift verification.</p></td></tr>
                </table>
                <?php submit_button(); ?>
            </form>
            <h2>Connection endpoint</h2>
            <p><code><?php echo esc_html(rest_url('seo-workflow-bridge/v1/execute')); ?></code></p>
            <h2>Article preparation endpoint</h2>
            <p><code><?php echo esc_html(rest_url('seo-workflow-bridge/v1/prepare')); ?></code></p>
            <h2>Article publication endpoint</h2>
            <p><code><?php echo esc_html(rest_url('seo-workflow-bridge/v1/publish')); ?></code></p>
        </div>
        <?php
    }
}
