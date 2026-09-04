<?php

declare(strict_types=1);

if (!defined('ABSPATH')) {
    exit;
}

final class SEO_Workflow_Bridge_OIDC_Verifier
{
    private const ISSUER = 'https://token.actions.githubusercontent.com';
    private const OPENID_CONFIGURATION = 'https://token.actions.githubusercontent.com/.well-known/openid-configuration';
    private const CONFIG_TRANSIENT = 'seo_workflow_bridge_oidc_config';
    private const JWKS_TRANSIENT = 'seo_workflow_bridge_oidc_jwks';

    /** @return array<string,mixed>|WP_Error */
    public function verify(string $jwt, array $settings)
    {
        $parts = explode('.', $jwt);
        if (count($parts) !== 3) {
            return new WP_Error('invalid_jwt', 'Malformed GitHub OIDC token.');
        }

        [$encoded_header, $encoded_payload, $encoded_signature] = $parts;
        $header = $this->decode_json_segment($encoded_header);
        $claims = $this->decode_json_segment($encoded_payload);
        $signature = $this->base64url_decode($encoded_signature);

        if (!is_array($header) || !is_array($claims) || $signature === false) {
            return new WP_Error('invalid_jwt', 'Unable to decode GitHub OIDC token.');
        }
        if (($header['alg'] ?? '') !== 'RS256' || empty($header['kid'])) {
            return new WP_Error('invalid_jwt_algorithm', 'Unexpected GitHub OIDC token algorithm or key id.');
        }

        $public_key = $this->public_key_for_kid((string)$header['kid']);
        if (is_wp_error($public_key)) {
            return $public_key;
        }

        $verified = openssl_verify(
            $encoded_header . '.' . $encoded_payload,
            $signature,
            $public_key,
            OPENSSL_ALGO_SHA256
        );
        if ($verified !== 1) {
            return new WP_Error('invalid_jwt_signature', 'GitHub OIDC token signature verification failed.');
        }

        $now = time();
        $leeway = 60;
        if (($claims['iss'] ?? '') !== self::ISSUER) {
            return new WP_Error('invalid_issuer', 'Unexpected OIDC issuer.');
        }
        if ((string)($claims['aud'] ?? '') !== (string)($settings['audience'] ?? '')) {
            return new WP_Error('invalid_audience', 'Unexpected OIDC audience.');
        }
        if (!isset($claims['exp']) || (int)$claims['exp'] < ($now - $leeway)) {
            return new WP_Error('expired_token', 'OIDC token has expired.');
        }
        if (isset($claims['nbf']) && (int)$claims['nbf'] > ($now + $leeway)) {
            return new WP_Error('token_not_yet_valid', 'OIDC token is not yet valid.');
        }
        if (isset($claims['iat']) && (int)$claims['iat'] > ($now + $leeway)) {
            return new WP_Error('invalid_iat', 'OIDC token issue time is in the future.');
        }

        $expected_repository_id = trim((string)($settings['repository_id'] ?? ''));
        if ($expected_repository_id === '' || (string)($claims['repository_id'] ?? '') !== $expected_repository_id) {
            return new WP_Error('repository_mismatch', 'OIDC repository_id does not match the configured repository.');
        }

        $expected_owner_id = trim((string)($settings['repository_owner_id'] ?? ''));
        if ($expected_owner_id !== '' && (string)($claims['repository_owner_id'] ?? '') !== $expected_owner_id) {
            return new WP_Error('repository_owner_mismatch', 'OIDC repository_owner_id does not match the configured owner.');
        }

        $expected_repository = trim((string)($settings['repository'] ?? ''));
        if ($expected_repository !== '' && (string)($claims['repository'] ?? '') !== $expected_repository) {
            return new WP_Error('repository_name_mismatch', 'OIDC repository name does not match the configured repository.');
        }

        $allowed_events = $settings['allowed_event_names'] ?? ['issues', 'workflow_dispatch', 'schedule'];
        if (!is_array($allowed_events) || $allowed_events === []) {
            $allowed_events = ['issues', 'workflow_dispatch', 'schedule'];
        }
        $event_name = (string)($claims['event_name'] ?? '');
        if (!in_array($event_name, array_map('strval', $allowed_events), true)) {
            return new WP_Error('event_mismatch', 'OIDC event_name is not allowed for this Bridge operation.');
        }

        $allowed_workflows = $settings['allowed_workflow_refs'] ?? [];
        if (!is_array($allowed_workflows) || $allowed_workflows === []) {
            $legacy_workflow = trim((string)($settings['workflow_ref'] ?? ''));
            $allowed_workflows = $legacy_workflow !== '' ? [$legacy_workflow] : [];
            if ($legacy_workflow !== '') {
                $extra_workflows = [];
                if ($event_name === 'workflow_dispatch') {
                    $extra_workflows = [
                        'linkedin-publish-relay.yml',
                        'facebook-publish-relay.yml',
                        'social-connection-health.yml',
                    ];
                } elseif ($event_name === 'schedule') {
                    // Scheduled OIDC is intentionally narrower: only the read-only
                    // social connection health workflow may use this event type.
                    $extra_workflows = ['social-connection-health.yml'];
                }
                foreach ($extra_workflows as $relay_file) {
                    $scheduled_workflow = preg_replace(
                        '#/\.github/workflows/[^@]+@#',
                        '/.github/workflows/' . $relay_file . '@',
                        $legacy_workflow,
                        1
                    );
                    if (is_string($scheduled_workflow) && $scheduled_workflow !== '' && $scheduled_workflow !== $legacy_workflow) {
                        $allowed_workflows[] = $scheduled_workflow;
                    }
                }
            }
        }
        $allowed_workflows = array_values(array_unique(array_filter(array_map('strval', $allowed_workflows), static function (string $value): bool {
            return trim($value) !== '';
        })));
        $actual_workflow_ref = (string)($claims['job_workflow_ref'] ?? ($claims['workflow_ref'] ?? ''));
        if ($allowed_workflows === [] || !in_array($actual_workflow_ref, $allowed_workflows, true)) {
            return new WP_Error('workflow_mismatch', 'OIDC workflow reference is not allowed for this Bridge operation.');
        }

        if (!empty($settings['require_private_repository']) && ($claims['repository_visibility'] ?? '') !== 'private') {
            return new WP_Error('repository_visibility_mismatch', 'The relay requires a private GitHub repository.');
        }

        return $claims;
    }

    /** @return array<string,mixed>|false */
    private function decode_json_segment(string $segment)
    {
        $decoded = $this->base64url_decode($segment);
        if ($decoded === false) {
            return false;
        }
        $data = json_decode($decoded, true);
        return is_array($data) ? $data : false;
    }

    /** @return string|false */
    private function base64url_decode(string $value)
    {
        $remainder = strlen($value) % 4;
        if ($remainder !== 0) {
            $value .= str_repeat('=', 4 - $remainder);
        }
        return base64_decode(strtr($value, '-_', '+/'), true);
    }

    /** @return resource|OpenSSLAsymmetricKey|WP_Error */
    private function public_key_for_kid(string $kid)
    {
        $jwks = get_transient(self::JWKS_TRANSIENT);
        if (!is_array($jwks)) {
            $configuration = get_transient(self::CONFIG_TRANSIENT);
            if (!is_array($configuration)) {
                $configuration = $this->fetch_json(self::OPENID_CONFIGURATION);
                if (is_wp_error($configuration)) {
                    return $configuration;
                }
                set_transient(self::CONFIG_TRANSIENT, $configuration, 12 * HOUR_IN_SECONDS);
            }
            $jwks_uri = (string)($configuration['jwks_uri'] ?? '');
            if ($jwks_uri === '' || strpos($jwks_uri, 'https://token.actions.githubusercontent.com/') !== 0) {
                return new WP_Error('invalid_jwks_uri', 'Unexpected GitHub OIDC JWKS URI.');
            }
            $jwks = $this->fetch_json($jwks_uri);
            if (is_wp_error($jwks)) {
                return $jwks;
            }
            set_transient(self::JWKS_TRANSIENT, $jwks, 12 * HOUR_IN_SECONDS);
        }

        foreach (($jwks['keys'] ?? []) as $jwk) {
            if (!is_array($jwk) || (string)($jwk['kid'] ?? '') !== $kid) {
                continue;
            }
            if (($jwk['kty'] ?? '') !== 'RSA' || empty($jwk['n']) || empty($jwk['e'])) {
                return new WP_Error('invalid_jwk', 'Unexpected GitHub OIDC JWK.');
            }
            $pem = $this->rsa_jwk_to_pem((string)$jwk['n'], (string)$jwk['e']);
            if (is_wp_error($pem)) {
                return $pem;
            }
            $key = openssl_pkey_get_public($pem);
            if ($key === false) {
                return new WP_Error('invalid_public_key', 'Unable to load GitHub OIDC public key.');
            }
            return $key;
        }

        delete_transient(self::JWKS_TRANSIENT);
        return new WP_Error('unknown_kid', 'GitHub OIDC signing key was not found. Retry once after key cache refresh.');
    }

    /** @return array<string,mixed>|WP_Error */
    private function fetch_json(string $url)
    {
        $response = wp_remote_get($url, [
            'timeout' => 10,
            'redirection' => 2,
            'headers' => ['Accept' => 'application/json'],
            'user-agent' => 'SEO-Workflow-Bridge/' . SEO_WORKFLOW_BRIDGE_VERSION,
        ]);
        if (is_wp_error($response)) {
            return $response;
        }
        $status = (int)wp_remote_retrieve_response_code($response);
        if ($status !== 200) {
            return new WP_Error('oidc_fetch_failed', 'GitHub OIDC metadata request returned HTTP ' . $status . '.');
        }
        $data = json_decode((string)wp_remote_retrieve_body($response), true);
        if (!is_array($data)) {
            return new WP_Error('oidc_json_failed', 'GitHub OIDC metadata response was not valid JSON.');
        }
        return $data;
    }

    /** @return string|WP_Error */
    private function rsa_jwk_to_pem(string $n, string $e)
    {
        $modulus = $this->base64url_decode($n);
        $exponent = $this->base64url_decode($e);
        if ($modulus === false || $exponent === false) {
            return new WP_Error('invalid_jwk_encoding', 'Unable to decode RSA JWK parameters.');
        }

        $rsa_public_key = $this->der_sequence(
            $this->der_integer($modulus) . $this->der_integer($exponent)
        );
        $algorithm_identifier = $this->der_sequence(
            hex2bin('06092a864886f70d010101') . "\x05\x00"
        );
        $subject_public_key_info = $this->der_sequence(
            $algorithm_identifier . $this->der_bit_string($rsa_public_key)
        );

        return "-----BEGIN PUBLIC KEY-----\n" .
            chunk_split(base64_encode($subject_public_key_info), 64, "\n") .
            "-----END PUBLIC KEY-----\n";
    }

    private function der_integer(string $bytes): string
    {
        $bytes = ltrim($bytes, "\x00");
        if ($bytes === '') {
            $bytes = "\x00";
        }
        if ((ord($bytes[0]) & 0x80) !== 0) {
            $bytes = "\x00" . $bytes;
        }
        return "\x02" . $this->der_length(strlen($bytes)) . $bytes;
    }

    private function der_sequence(string $bytes): string
    {
        return "\x30" . $this->der_length(strlen($bytes)) . $bytes;
    }

    private function der_bit_string(string $bytes): string
    {
        $bytes = "\x00" . $bytes;
        return "\x03" . $this->der_length(strlen($bytes)) . $bytes;
    }

    private function der_length(int $length): string
    {
        if ($length < 128) {
            return chr($length);
        }
        $encoded = '';
        while ($length > 0) {
            $encoded = chr($length & 0xff) . $encoded;
            $length >>= 8;
        }
        return chr(0x80 | strlen($encoded)) . $encoded;
    }
}
