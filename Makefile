# Invoked by `sam build` via `Metadata: BuildMethod: makefile` in template.yaml.
# SAM sets $(ARTIFACTS_DIR) to .aws-sam/build/DailyBriefFunction/ and runs this
# from the project root (where pyproject.toml and uv.lock live).

build-DailyBriefFunction:
	uv export --no-dev --no-hashes --format requirements-txt > requirements.txt
	uv pip install -r requirements.txt --target "$(ARTIFACTS_DIR)" --quiet
	cp -r daily_brief "$(ARTIFACTS_DIR)/"
	@echo "==> Stripping deployment bloat..."
	@# Python bytecode caches — regenerated on first run, no benefit to shipping
	find "$(ARTIFACTS_DIR)" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find "$(ARTIFACTS_DIR)" -type f -name "*.pyc" -delete 2>/dev/null || true
	@# boto3 + botocore are provided by the Lambda Python runtime (~40 MB saved).
	@# Kept in pyproject.toml so the handler can be run/tested locally.
	rm -rf "$(ARTIFACTS_DIR)/boto3" "$(ARTIFACTS_DIR)/botocore"
	rm -rf "$(ARTIFACTS_DIR)"/boto3-*.dist-info "$(ARTIFACTS_DIR)"/botocore-*.dist-info
	@SIZE_KB=$$(du -sk "$(ARTIFACTS_DIR)" | cut -f1); \
	SIZE_MB=$$((SIZE_KB / 1024)); \
	echo "Package size: $${SIZE_MB} MB (limit: 250 MB unzipped)"; \
	if [ "$$SIZE_KB" -ge 240000 ]; then \
		echo "ERROR: Package is $${SIZE_MB} MB — too close to the 250 MB Lambda zip limit."; \
		exit 1; \
	fi
