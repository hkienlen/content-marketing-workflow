<?php
/**
 * Plugin Name: SEO Workflow Bridge
 * Description: Narrow WordPress bridge for repository-backed editorial workflows authenticated with GitHub Actions OIDC.
 * Version: 0.11.0
 * Requires at least: 6.9
 * Requires PHP: 7.4
 * Author: Editorial Workflow
 * Previous release Version: 0.10.0
 */

declare(strict_types=1);

if (!defined('ABSPATH')) {
    exit;
}

define('SEO_WORKFLOW_BRIDGE_VERSION', '0.11.0');
define('SEO_WORKFLOW_BRIDGE_FILE', __FILE__);
define('SEO_WORKFLOW_BRIDGE_DIR', plugin_dir_path(__FILE__));

require_once SEO_WORKFLOW_BRIDGE_DIR . 'includes/class-oidc-verifier.php';
require_once SEO_WORKFLOW_BRIDGE_DIR . 'includes/class-rest-controller.php';
require_once SEO_WORKFLOW_BRIDGE_DIR . 'includes/class-preparation-controller.php';
require_once SEO_WORKFLOW_BRIDGE_DIR . 'includes/class-publication-controller.php';
require_once SEO_WORKFLOW_BRIDGE_DIR . 'includes/class-divi-converter-controller.php';
require_once SEO_WORKFLOW_BRIDGE_DIR . 'includes/class-linkedin-oauth-controller.php';
// The generic non-publishing media identity probe remains available for
// controlled diagnostics; historical pilot-specific dry-run/live-gate payloads
// are deliberately excluded from the distributable plugin.
require_once SEO_WORKFLOW_BRIDGE_DIR . 'includes/class-linkedin-media-probe.php';
require_once SEO_WORKFLOW_BRIDGE_DIR . 'includes/class-linkedin-scheduled-publish.php';
require_once SEO_WORKFLOW_BRIDGE_DIR . 'includes/class-facebook-page-controller.php';
require_once SEO_WORKFLOW_BRIDGE_DIR . 'includes/class-facebook-page-scheduled-publish.php';
require_once SEO_WORKFLOW_BRIDGE_DIR . 'includes/class-facebook-page-publication-verifier.php';
require_once SEO_WORKFLOW_BRIDGE_DIR . 'includes/class-admin.php';
require_once SEO_WORKFLOW_BRIDGE_DIR . 'includes/class-linkedin-admin.php';
require_once SEO_WORKFLOW_BRIDGE_DIR . 'includes/class-facebook-page-admin.php';

add_action('plugins_loaded', static function (): void {
    $verifier = new SEO_Workflow_Bridge_OIDC_Verifier();
    (new SEO_Workflow_Bridge_REST_Controller($verifier))->register();
    (new SEO_Workflow_Bridge_Preparation_Controller($verifier))->register();
    (new SEO_Workflow_Bridge_Publication_Controller($verifier))->register();
    (new SEO_Workflow_Bridge_Divi_Converter_Controller($verifier))->register();
    (new SEO_Workflow_Bridge_LinkedIn_Controller())->register();
    (new SEO_Workflow_Bridge_LinkedIn_Scheduled_Publish($verifier))->register();
    (new SEO_Workflow_Bridge_Facebook_Page_Controller())->register();
    (new SEO_Workflow_Bridge_Facebook_Page_Scheduled_Publish($verifier))->register();
    (new SEO_Workflow_Bridge_Facebook_Page_Publication_Verifier($verifier))->register();
    if (is_admin()) {
        (new SEO_Workflow_Bridge_Admin())->register();
        (new SEO_Workflow_Bridge_LinkedIn_Admin())->register();
        (new SEO_Workflow_Bridge_Facebook_Page_Admin())->register();
    }
});
