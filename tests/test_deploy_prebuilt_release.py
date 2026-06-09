from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_prod_compose_uses_prebuilt_app_image() -> None:
    compose = (ROOT / "deploy/docker-compose.prod.yml").read_text()

    assert "image: ${APP_IMAGE}" in compose
    assert "dockerfile: Dockerfile" not in compose
    assert "--no-build" in compose


def test_git_pull_deploy_never_builds_on_prod_host() -> None:
    script = (ROOT / "deploy/git-pull-deploy.sh").read_text()

    assert "up -d --no-build" in script
    assert "up -d --build" not in script
    assert "docker build" not in script
    assert "require_image \"APP_IMAGE\"" in script
    assert "rollback_app_image" in script


def test_auto_deploy_timer_is_disabled_by_default() -> None:
    script = (ROOT / "deploy/install-auto-deploy.sh").read_text()

    assert 'ENABLE_AUTO_DEPLOY="${ENABLE_AUTO_DEPLOY:-0}"' in script
    assert "systemctl disable --now" in script


def test_prebuilt_release_loads_image_before_deploy() -> None:
    script = (ROOT / "deploy/release-prebuilt-app.sh").read_text()

    assert "docker buildx build --platform" in script
    assert "docker save" in script
    assert "docker load -i" in script
    assert 'set_env_value "APP_IMAGE"' in script
    assert "./deploy/git-pull-deploy.sh" in script
