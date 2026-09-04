<?php

declare(strict_types=1);

if (!defined('ABSPATH')) {
    exit;
}

/**
 * Optional, read/transform-only integration with Divi's official conversion API.
 *
 * This controller never writes posts or metadata. It accepts repository-backed
 * Divi 4 shortcode content from the authenticated relay and returns the content
 * produced by Divi's own D4 -> D5 converter. Article persistence remains the
 * responsibility of the normal preparation controller and its existing gate.
 */
final class SEO_Workflow_Bridge_Divi_Converter_Controller
{
    private const OPTION = 'seo_workflow_bridge_settings';
    private const MAX_CONTENT_BYTES = 2097152;

    private SEO_Workflow_Bridge_OIDC_Verifier $verifier;

    public function __construct(SEO_Workflow_Bridge_OIDC_Verifier $verifier)
    {
        $this->verifier = $verifier;
    }

    public function register(): void
    {
        add_action('rest_api_init', function (): void {
            register_rest_route('seo-workflow-bridge/v1', '/divi-convert', [
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
        if (empty($settings['allow_article_prepare'])) {
            return $this->error('article_prepare_disabled', 'Article draft preparation is disabled.', 403);
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

        $payload = is_array($body['payload'] ?? null) ? $body['payload'] : [];
        $content = (string)($payload['content'] ?? '');
        if ($content === '') {
            return $this->error('empty_divi_content', 'Divi conversion content cannot be empty.', 400);
        }
        if (strlen($content) > self::MAX_CONTENT_BYTES) {
            return $this->error('divi_content_too_large', 'Divi conversion content exceeds the bridge limit.', 413);
        }
        if (!preg_match('/\[et_pb_(?:section|row|column|text)\b/', $content)) {
            return $this->error('not_divi4_layout', 'The conversion input does not contain the expected Divi 4 layout shortcodes.', 400);
        }

        $class = '\\ET\\Builder\\Packages\\Conversion\\Conversion';
        if (!class_exists($class) || !is_callable([$class, 'maybeConvertContent'])) {
            return $this->error(
                'divi_converter_unavailable',
                'Divi official Conversion::maybeConvertContent() is not available on this WordPress site.',
                503
            );
        }

        try {
            $converted = $class::maybeConvertContent($content, true, null);
        } catch (Throwable $exception) {
            return $this->error('divi_conversion_failed', 'Divi conversion failed: ' . $exception->getMessage(), 500);
        }

        if (!is_string($converted) || $converted === '') {
            return $this->error('divi_conversion_empty', 'Divi returned empty converted content.', 500);
        }
        if ($converted === $content) {
            return $this->error('divi_conversion_unchanged', 'Divi returned the legacy content unchanged.', 500);
        }
        if (preg_match('/\[et_pb_(?:section|row|column|text)\b/', $converted)) {
            return $this->error('divi_conversion_incomplete', 'Core Divi 4 layout shortcodes remain after conversion.', 500);
        }
        if (strpos($converted, '<!-- wp:divi/') === false) {
            return $this->error('divi_conversion_not_native', 'Divi conversion result does not contain native Divi block storage.', 500);
        }

        return new WP_REST_Response([
            'ok' => true,
            'schema_version' => 1,
            'request_id' => (string)$body['request_id'],
            'operation' => 'divi_d4_to_d5',
            'site_url' => site_url(),
            'result' => [
                'content' => $converted,
                'input_sha256' => hash('sha256', $content),
                'output_sha256' => hash('sha256', $converted),
                'conversion_changed' => true,
                'converter' => 'ET\\Builder\\Packages\\Conversion\\Conversion::maybeConvertContent',
            ],
            'oidc' => [
                'repository_id' => (string)($claims['repository_id'] ?? ''),
                'run_id' => (string)($claims['run_id'] ?? ''),
                'workflow_ref' => (string)($claims['job_workflow_ref'] ?? ($claims['workflow_ref'] ?? '')),
            ],
        ], 200);
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
        if ((string)($body['operation'] ?? '') !== 'divi_d4_to_d5') {
            return new WP_Error('invalid_operation', 'Only divi_d4_to_d5 is supported by this endpoint.');
        }
        $issued_at = strtotime((string)($body['issued_at'] ?? ''));
        if ($issued_at === false || abs(time() - $issued_at) > HOUR_IN_SECONDS) {
            return new WP_Error('stale_request', 'Relay request issued_at must be within one hour of server time.');
        }
        if (!is_array($body['payload'] ?? null)) {
            return new WP_Error('invalid_payload', 'payload must be an object.');
        }
        return true;
    }

    /** @return array<string,mixed> */
    private function settings(): array
    {
        $settings = get_option(self::OPTION, []);
        return is_array($settings) ? $settings : [];
    }

    private function error(string $code, string $message, int $status): WP_REST_Response
    {
        return new WP_REST_Response([
            'ok' => false,
            'schema_version' => 1,
            'error' => ['code' => $code, 'message' => $message],
        ], $status);
    }
}
