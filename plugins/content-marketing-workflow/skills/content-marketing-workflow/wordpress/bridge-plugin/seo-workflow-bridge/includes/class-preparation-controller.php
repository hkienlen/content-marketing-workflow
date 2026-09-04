<?php

declare(strict_types=1);

if (!defined('ABSPATH')) {
    exit;
}

final class SEO_Workflow_Bridge_Preparation_Controller
{
    private const OPTION = 'seo_workflow_bridge_settings';
    private const REQUEST_TTL = 86400;
    private const MAX_MEDIA_BYTES = 8388608;

    private const MANAGED_POST_META = '_seo_workflow_bridge_managed';
    private const MANIFEST_PATH_META = '_seo_workflow_bridge_manifest_path';
    private const SOURCE_COMMIT_META = '_seo_workflow_bridge_source_commit';
    private const SOURCE_ARTICLE_PATH_META = '_seo_workflow_bridge_source_article_path';
    private const SOURCE_ARTICLE_SHA_META = '_seo_workflow_bridge_source_article_sha256';

    private const ASSET_PATH_META = '_seo_workflow_bridge_asset_path';
    private const ASSET_SHA_META = '_seo_workflow_bridge_asset_sha256';
    private const ASSET_KEY_META = '_seo_workflow_bridge_asset_key';
    private const ASSET_MANIFEST_META = '_seo_workflow_bridge_asset_manifest_path';

    private SEO_Workflow_Bridge_OIDC_Verifier $verifier;

    public function __construct(SEO_Workflow_Bridge_OIDC_Verifier $verifier)
    {
        $this->verifier = $verifier;
    }

    public function register(): void
    {
        add_action('rest_api_init', function (): void {
            register_rest_route('seo-workflow-bridge/v1', '/prepare', [
                'methods' => 'POST',
                'callback' => [$this, 'execute'],
                'permission_callback' => '__return_true',
            ]);
        });
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
            case 'media_upsert':
                if (empty($settings['allow_article_prepare'])) {
                    return new WP_Error('article_prepare_disabled', 'Article draft preparation is disabled.');
                }
                return $this->media_upsert($payload);
            case 'article_prepare':
                if (empty($settings['allow_article_prepare'])) {
                    return new WP_Error('article_prepare_disabled', 'Article draft preparation is disabled.');
                }
                return $this->article_prepare($payload, $settings);
            case 'article_read':
                if (empty($settings['allow_content_read'])) {
                    return new WP_Error('content_read_disabled', 'Content read is disabled in the bridge settings.');
                }
                return $this->article_read($payload, $settings);
            default:
                return new WP_Error('unsupported_operation', 'Unsupported preparation operation.');
        }
    }

    /** @return array<string,mixed>|WP_Error */
    private function media_upsert(array $payload)
    {
        $manifest_path = $this->repository_path((string)($payload['manifest_path'] ?? ''));
        $asset_path = $this->repository_path((string)($payload['repository_path'] ?? ''));
        $asset_key = sanitize_key((string)($payload['asset_key'] ?? ''));
        $sha256 = strtolower((string)($payload['sha256'] ?? ''));
        $filename = sanitize_file_name((string)($payload['filename'] ?? ''));
        $mime_type = sanitize_mime_type((string)($payload['mime_type'] ?? ''));
        $encoded = (string)($payload['content_base64'] ?? '');

        if ($manifest_path === '' || $asset_path === '' || $asset_key === '' || $filename === '') {
            return new WP_Error('invalid_media_identity', 'Media manifest/path/key/filename are required.');
        }
        if (!preg_match('/^[a-f0-9]{64}$/', $sha256)) {
            return new WP_Error('invalid_media_sha256', 'Media sha256 must be a lowercase SHA-256 hex digest.');
        }

        $bytes = base64_decode($encoded, true);
        if ($bytes === false || $bytes === '') {
            return new WP_Error('invalid_media_content', 'Media content_base64 is invalid or empty.');
        }
        if (strlen($bytes) > self::MAX_MEDIA_BYTES) {
            return new WP_Error('media_too_large', 'Media exceeds the bridge maximum size.');
        }
        if (!hash_equals($sha256, hash('sha256', $bytes))) {
            return new WP_Error('media_hash_mismatch', 'Media bytes do not match the declared sha256.');
        }

        $filetype = wp_check_filetype($filename);
        $detected_mime = (string)($filetype['type'] ?? '');
        $allowed_mimes = ['image/jpeg', 'image/png', 'image/webp', 'image/gif'];
        if ($detected_mime === '' || !in_array($detected_mime, $allowed_mimes, true)) {
            return new WP_Error('unsupported_media_type', 'Only JPEG, PNG, WebP and GIF images are supported by V1 media preparation.');
        }
        if ($mime_type !== '' && $mime_type !== $detected_mime) {
            return new WP_Error('media_mime_mismatch', 'Declared media MIME type does not match the filename.');
        }

        $existing = get_posts([
            'post_type' => 'attachment',
            'post_status' => 'inherit',
            'numberposts' => 2,
            'meta_key' => self::ASSET_PATH_META,
            'meta_value' => $asset_path,
            'suppress_filters' => false,
        ]);
        if (count($existing) > 1) {
            return new WP_Error('duplicate_managed_asset', 'Multiple bridge-managed attachments use the same repository asset path.');
        }
        if (count($existing) === 1) {
            $attachment_id = (int)$existing[0]->ID;
            $existing_sha = (string)get_post_meta($attachment_id, self::ASSET_SHA_META, true);
            if (!hash_equals($sha256, $existing_sha)) {
                return new WP_Error('managed_asset_changed', 'A bridge-managed attachment exists for this path with different bytes. V1 refuses implicit replacement.');
            }
            update_post_meta($attachment_id, self::ASSET_KEY_META, $asset_key);
            update_post_meta($attachment_id, self::ASSET_MANIFEST_META, $manifest_path);
            $this->update_attachment_fields($attachment_id, $payload);
            return $this->attachment_result($attachment_id, true);
        }

        $upload = wp_upload_bits($filename, null, $bytes);
        if (!empty($upload['error'])) {
            return new WP_Error('media_upload_failed', (string)$upload['error']);
        }

        $attachment_id = wp_insert_attachment([
            'post_mime_type' => $detected_mime,
            'post_title' => sanitize_text_field((string)($payload['title'] ?? pathinfo($filename, PATHINFO_FILENAME))),
            'post_content' => '',
            'post_excerpt' => sanitize_textarea_field((string)($payload['caption'] ?? '')),
            'post_status' => 'inherit',
        ], (string)$upload['file'], 0, true);
        if (is_wp_error($attachment_id)) {
            @unlink((string)$upload['file']);
            return $attachment_id;
        }

        require_once ABSPATH . 'wp-admin/includes/image.php';
        $metadata = wp_generate_attachment_metadata((int)$attachment_id, (string)$upload['file']);
        if (is_array($metadata)) {
            wp_update_attachment_metadata((int)$attachment_id, $metadata);
        }
        update_post_meta((int)$attachment_id, self::ASSET_PATH_META, $asset_path);
        update_post_meta((int)$attachment_id, self::ASSET_SHA_META, $sha256);
        update_post_meta((int)$attachment_id, self::ASSET_KEY_META, $asset_key);
        update_post_meta((int)$attachment_id, self::ASSET_MANIFEST_META, $manifest_path);
        $this->update_attachment_fields((int)$attachment_id, $payload);

        return $this->attachment_result((int)$attachment_id, false);
    }

    private function update_attachment_fields(int $attachment_id, array $payload): void
    {
        wp_update_post([
            'ID' => $attachment_id,
            'post_title' => sanitize_text_field((string)($payload['title'] ?? get_the_title($attachment_id))),
            'post_excerpt' => sanitize_textarea_field((string)($payload['caption'] ?? '')),
        ]);
        update_post_meta($attachment_id, '_wp_attachment_image_alt', sanitize_text_field((string)($payload['alt'] ?? '')));
    }

    /** @return array<string,mixed> */
    private function attachment_result(int $attachment_id, bool $reused): array
    {
        return [
            'id' => $attachment_id,
            'url' => (string)wp_get_attachment_url($attachment_id),
            'reused' => $reused,
            'sha256' => (string)get_post_meta($attachment_id, self::ASSET_SHA_META, true),
            'repository_path' => (string)get_post_meta($attachment_id, self::ASSET_PATH_META, true),
        ];
    }

    /** @return array<string,mixed>|WP_Error */
    private function article_prepare(array $payload, array $settings)
    {
        $manifest_path = $this->repository_path((string)($payload['manifest_path'] ?? ''));
        $source_commit = strtolower((string)($payload['source_commit'] ?? ''));
        $source_article_path = $this->repository_path((string)($payload['source_article_path'] ?? ''));
        $source_article_sha = strtolower((string)($payload['source_article_sha256'] ?? ''));
        $post_type = (string)($payload['post_type'] ?? 'post');
        $title = sanitize_text_field((string)($payload['title'] ?? ''));
        $slug = sanitize_title((string)($payload['slug'] ?? ''));

        if ($manifest_path === '' || $source_article_path === '' || !preg_match('/^[a-f0-9]{40}$/', $source_commit) || !preg_match('/^[a-f0-9]{64}$/', $source_article_sha)) {
            return new WP_Error('invalid_article_source', 'A valid manifest path, source article path, commit SHA and article SHA-256 are required.');
        }
        if (!in_array($post_type, ['post', 'page'], true)) {
            return new WP_Error('unsupported_post_type', 'V1 article preparation supports only posts and pages.');
        }
        if ($title === '' || $slug === '') {
            return new WP_Error('invalid_article_identity', 'Article title and slug are required.');
        }

        $taxonomy_validation = $this->validate_taxonomies($payload, $settings);
        if (is_wp_error($taxonomy_validation)) {
            return $taxonomy_validation;
        }
        $meta_validation = $this->validate_allowed_post_meta($payload, $settings);
        if (is_wp_error($meta_validation)) {
            return $meta_validation;
        }

        $managed = get_posts([
            'post_type' => $post_type,
            'post_status' => ['draft', 'pending', 'private', 'future', 'publish'],
            'numberposts' => 2,
            'meta_key' => self::SOURCE_ARTICLE_PATH_META,
            'meta_value' => $source_article_path,
            'suppress_filters' => false,
        ]);
        if (count($managed) > 1) {
            return new WP_Error('duplicate_managed_draft', 'Multiple bridge-managed WordPress posts use the same repository article path.');
        }

        $post_id = 0;
        $created = false;
        if (count($managed) === 1) {
            $post_id = (int)$managed[0]->ID;
            if (get_post_meta($post_id, self::MANAGED_POST_META, true) !== '1') {
                return new WP_Error('managed_marker_missing', 'The source-path matched post is missing the bridge-managed marker.');
            }
            if ((string)$managed[0]->post_status !== 'draft') {
                return new WP_Error('managed_post_not_draft', 'The bridge refuses to modify a managed article that is no longer a draft.');
            }
        } else {
            $slug_match = get_page_by_path($slug, OBJECT, $post_type);
            if ($slug_match instanceof WP_Post) {
                return new WP_Error('slug_conflict_unmanaged', 'A WordPress post already uses this slug but is not bridge-managed for this source article.');
            }
            $created = true;
        }

        $author_id = 0;
        $author_login = sanitize_user((string)($payload['author_login'] ?? ''), true);
        if ($author_login !== '') {
            $author = get_user_by('login', $author_login);
            if (!$author instanceof WP_User) {
                return new WP_Error('author_not_found', 'Configured WordPress author login was not found.');
            }
            $author_id = (int)$author->ID;
        }

        $postarr = [
            'post_type' => $post_type,
            'post_status' => 'draft',
            'post_title' => $title,
            'post_name' => $slug,
            'post_content' => (string)($payload['content'] ?? ''),
            'post_excerpt' => sanitize_textarea_field((string)($payload['excerpt'] ?? '')),
        ];
        if ($author_id > 0) {
            $postarr['post_author'] = $author_id;
        }
        if ($post_id > 0) {
            $postarr['ID'] = $post_id;
            $result_id = wp_update_post(wp_slash($postarr), true);
        } else {
            $result_id = wp_insert_post(wp_slash($postarr), true);
        }
        if (is_wp_error($result_id)) {
            return $result_id;
        }
        $post_id = (int)$result_id;

        update_post_meta($post_id, self::MANAGED_POST_META, '1');
        update_post_meta($post_id, self::MANIFEST_PATH_META, $manifest_path);
        update_post_meta($post_id, self::SOURCE_COMMIT_META, $source_commit);
        update_post_meta($post_id, self::SOURCE_ARTICLE_PATH_META, $source_article_path);
        update_post_meta($post_id, self::SOURCE_ARTICLE_SHA_META, $source_article_sha);

        $taxonomy_result = $this->apply_taxonomies($post_id, $payload, $settings);
        if (is_wp_error($taxonomy_result)) {
            return $taxonomy_result;
        }
        $meta_result = $this->apply_allowed_post_meta($post_id, $payload, $settings);
        if (is_wp_error($meta_result)) {
            return $meta_result;
        }

        $featured_media_id = (int)($payload['featured_media_id'] ?? 0);
        if ($featured_media_id > 0) {
            if (!$this->is_bridge_managed_attachment($featured_media_id)) {
                return new WP_Error('invalid_featured_media', 'Featured media must be a bridge-managed attachment.');
            }
            set_post_thumbnail($post_id, $featured_media_id);
            if ((int)get_post_thumbnail_id($post_id) !== $featured_media_id) {
                return new WP_Error('featured_media_failed', 'Unable to set the featured media on the prepared draft.');
            }
        }

        return [
            'id' => $post_id,
            'created' => $created,
            'status' => (string)get_post_status($post_id),
            'slug' => (string)get_post_field('post_name', $post_id),
            'title' => (string)get_post_field('post_title', $post_id),
            'featured_media_id' => (int)get_post_thumbnail_id($post_id),
            'manifest_path' => $manifest_path,
            'source_commit' => $source_commit,
            'source_article_path' => $source_article_path,
            'resolved_post_meta' => $meta_result,
            'resolved_taxonomies' => $taxonomy_result,
        ];
    }

    /** @return true|WP_Error */
    private function validate_allowed_post_meta(array $payload, array $settings)
    {
        $post_meta = $payload['post_meta'] ?? [];
        if (!is_array($post_meta)) {
            return new WP_Error('invalid_post_meta', 'post_meta must be an object.');
        }

        $allowed = array_fill_keys($this->csv_list((string)($settings['allowed_prepare_meta_keys'] ?? '')), true);
        $protected = [
            self::MANAGED_POST_META,
            self::MANIFEST_PATH_META,
            self::SOURCE_COMMIT_META,
            self::SOURCE_ARTICLE_PATH_META,
            self::SOURCE_ARTICLE_SHA_META,
            '_thumbnail_id',
            '_wp_attached_file',
            '_wp_attachment_metadata',
            '_edit_lock',
            '_edit_last',
        ];

        foreach ($post_meta as $key => $value) {
            $key = (string)$key;
            if (!isset($allowed[$key]) || in_array($key, $protected, true) || strpos($key, '_seo_workflow_bridge_') === 0) {
                return new WP_Error('post_meta_not_allowed', 'Preparation manifest requested a post meta key that is not allowed by bridge settings: ' . $key);
            }
            if (is_scalar($value) || $value === null) {
                continue;
            }
            $resolver_validation = $this->validate_meta_resolver($value, $settings);
            if (is_wp_error($resolver_validation)) {
                return $resolver_validation;
            }
        }
        return true;
    }

    /** @return true|WP_Error */
    private function validate_meta_resolver($value, array $settings)
    {
        if (!is_array($value) || array_keys($value) !== ['term_id_from_taxonomy']) {
            return new WP_Error('post_meta_value_unsupported', 'Post meta values must be scalar/null or a supported resolver object.');
        }
        $spec = $value['term_id_from_taxonomy'];
        if (!is_array($spec) || array_diff(array_keys($spec), ['taxonomy', 'slug']) !== [] || !isset($spec['taxonomy'], $spec['slug'])) {
            return new WP_Error('invalid_term_id_resolver', 'term_id_from_taxonomy requires only taxonomy and slug.');
        }
        $taxonomy = sanitize_key((string)$spec['taxonomy']);
        $slug = sanitize_title((string)$spec['slug']);
        $allowed = array_fill_keys($this->csv_list((string)($settings['allowed_prepare_taxonomies'] ?? '')), true);
        if ($taxonomy === '' || $slug === '' || !isset($allowed[$taxonomy]) || !taxonomy_exists($taxonomy)) {
            return new WP_Error('term_id_resolver_not_allowed', 'term_id_from_taxonomy references a taxonomy that is not allowed or does not exist.');
        }
        return true;
    }

    /** @return array<string,string>|WP_Error */
    private function apply_allowed_post_meta(int $post_id, array $payload, array $settings)
    {
        $validation = $this->validate_allowed_post_meta($payload, $settings);
        if (is_wp_error($validation)) {
            return $validation;
        }

        $resolved = [];
        foreach (($payload['post_meta'] ?? []) as $key => $value) {
            $key = (string)$key;
            if (is_array($value)) {
                $spec = $value['term_id_from_taxonomy'];
                $taxonomy = sanitize_key((string)$spec['taxonomy']);
                $slug = sanitize_title((string)$spec['slug']);
                $term = get_term_by('slug', $slug, $taxonomy);
                if (!$term instanceof WP_Term) {
                    return new WP_Error('term_id_resolver_not_found', 'term_id_from_taxonomy could not resolve the requested term.');
                }
                if (!has_term((int)$term->term_id, $taxonomy, $post_id)) {
                    return new WP_Error('term_id_resolver_not_assigned', 'term_id_from_taxonomy may only reference a term assigned to this prepared draft.');
                }
                $value = (string)$term->term_id;
            } elseif ($value === null) {
                $value = '';
            } else {
                $value = (string)$value;
            }
            update_post_meta($post_id, $key, $value);
            $resolved[$key] = $value;
        }
        return $resolved;
    }

    /** @return true|WP_Error */
    private function validate_taxonomies(array $payload, array $settings)
    {
        $groups = $payload['taxonomies'] ?? [];
        if (!is_array($groups)) {
            return new WP_Error('invalid_taxonomies', 'taxonomies must be an array.');
        }
        $allowed = array_fill_keys($this->csv_list((string)($settings['allowed_prepare_taxonomies'] ?? '')), true);
        foreach ($groups as $group) {
            if (!is_array($group)) {
                return new WP_Error('invalid_taxonomy_group', 'Each taxonomy group must be an object.');
            }
            $taxonomy = sanitize_key((string)($group['taxonomy'] ?? ''));
            if ($taxonomy === '' || !isset($allowed[$taxonomy]) || !taxonomy_exists($taxonomy)) {
                return new WP_Error('taxonomy_not_allowed', 'Preparation manifest requested a taxonomy that is not allowed or does not exist: ' . $taxonomy);
            }
            $terms = $group['terms'] ?? [];
            if (!is_array($terms)) {
                return new WP_Error('invalid_taxonomy_terms', 'Taxonomy terms must be an array.');
            }
            foreach ($terms as $term_data) {
                if (!is_array($term_data)) {
                    return new WP_Error('invalid_taxonomy_term', 'Each taxonomy term must be an object.');
                }
                if (sanitize_title((string)($term_data['slug'] ?? '')) === '' || sanitize_text_field((string)($term_data['name'] ?? '')) === '') {
                    return new WP_Error('invalid_taxonomy_term_identity', 'Taxonomy term name and slug are required.');
                }
            }
        }
        return true;
    }

    /** @return array<string,array<int,array<string,mixed>>>|WP_Error */
    private function apply_taxonomies(int $post_id, array $payload, array $settings)
    {
        $validation = $this->validate_taxonomies($payload, $settings);
        if (is_wp_error($validation)) {
            return $validation;
        }

        $resolved = [];
        foreach (($payload['taxonomies'] ?? []) as $group) {
            $taxonomy = sanitize_key((string)$group['taxonomy']);
            $term_ids = [];
            $summary = [];
            foreach ($group['terms'] as $term_data) {
                $slug = sanitize_title((string)$term_data['slug']);
                $name = sanitize_text_field((string)$term_data['name']);
                $term = get_term_by('slug', $slug, $taxonomy);
                if (!$term instanceof WP_Term) {
                    $inserted = wp_insert_term($name, $taxonomy, ['slug' => $slug]);
                    if (is_wp_error($inserted)) {
                        return $inserted;
                    }
                    $term_id = (int)$inserted['term_id'];
                } else {
                    $term_id = (int)$term->term_id;
                    $name = (string)$term->name;
                }
                $term_ids[] = $term_id;
                $summary[] = ['id' => $term_id, 'slug' => $slug, 'name' => $name];
            }
            $set = wp_set_object_terms($post_id, $term_ids, $taxonomy, false);
            if (is_wp_error($set)) {
                return $set;
            }
            $resolved[$taxonomy] = $summary;
        }
        return $resolved;
    }

    /** @return array<string,mixed>|WP_Error */
    private function article_read(array $payload, array $settings)
    {
        $post_id = (int)($payload['id'] ?? 0);
        $post = get_post($post_id);
        if (!$post instanceof WP_Post) {
            return new WP_Error('article_not_found', 'Prepared article was not found.');
        }
        if (get_post_meta($post_id, self::MANAGED_POST_META, true) !== '1') {
            return new WP_Error('article_not_managed', 'Only bridge-managed prepared articles can be read by this operation.');
        }

        $meta = [];
        foreach ($this->csv_list((string)($settings['allowed_prepare_meta_keys'] ?? '')) as $key) {
            if (metadata_exists('post', $post_id, $key)) {
                $meta[$key] = (string)get_post_meta($post_id, $key, true);
            }
        }

        $taxonomies = [];
        foreach ($this->csv_list((string)($settings['allowed_prepare_taxonomies'] ?? '')) as $taxonomy) {
            if (!taxonomy_exists($taxonomy)) {
                continue;
            }
            $terms = wp_get_object_terms($post_id, $taxonomy, ['fields' => 'all']);
            if (is_wp_error($terms)) {
                return $terms;
            }
            $taxonomies[$taxonomy] = array_map(static function (WP_Term $term): array {
                return ['id' => (int)$term->term_id, 'slug' => (string)$term->slug, 'name' => (string)$term->name];
            }, $terms);
        }

        return [
            'id' => $post_id,
            'post_type' => (string)$post->post_type,
            'status' => (string)$post->post_status,
            'slug' => (string)$post->post_name,
            'title' => (string)$post->post_title,
            'content' => (string)$post->post_content,
            'excerpt' => (string)$post->post_excerpt,
            'author_id' => (int)$post->post_author,
            'featured_media_id' => (int)get_post_thumbnail_id($post_id),
            'post_meta' => $meta,
            'taxonomies' => $taxonomies,
            'manifest_path' => (string)get_post_meta($post_id, self::MANIFEST_PATH_META, true),
            'source_commit' => (string)get_post_meta($post_id, self::SOURCE_COMMIT_META, true),
            'source_article_path' => (string)get_post_meta($post_id, self::SOURCE_ARTICLE_PATH_META, true),
            'source_article_sha256' => (string)get_post_meta($post_id, self::SOURCE_ARTICLE_SHA_META, true),
        ];
    }

    private function is_bridge_managed_attachment(int $attachment_id): bool
    {
        return get_post_type($attachment_id) === 'attachment'
            && get_post_meta($attachment_id, self::ASSET_PATH_META, true) !== ''
            && get_post_meta($attachment_id, self::ASSET_SHA_META, true) !== '';
    }

    private function repository_path(string $path): string
    {
        $path = trim(str_replace('\\', '/', $path));
        if ($path === '' || $path[0] === '/' || strpos($path, "\0") !== false || preg_match('#(^|/)\.\.(/|$)#', $path)) {
            return '';
        }
        if (!preg_match('#^[A-Za-z0-9._/@+,:=\-]+(?:/[A-Za-z0-9._/@+,:=\-]+)*$#', $path)) {
            return '';
        }
        return $path;
    }

    /** @return string[] */
    private function csv_list(string $value): array
    {
        $items = preg_split('/[,\r\n]+/', $value) ?: [];
        $result = [];
        foreach ($items as $item) {
            $item = trim($item);
            if ($item !== '') {
                $result[$item] = true;
            }
        }
        return array_keys($result);
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
        if (!in_array($operation, ['media_upsert', 'article_prepare', 'article_read'], true)) {
            return new WP_Error('invalid_operation', 'Invalid preparation operation.');
        }
        $issued_at = strtotime((string)($body['issued_at'] ?? ''));
        if ($issued_at === false || abs(time() - $issued_at) > HOUR_IN_SECONDS) {
            return new WP_Error('stale_request', 'Relay request issued_at must be within one hour of server time.');
        }
        return true;
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
