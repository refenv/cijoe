# Install cijoe into a pipx-managed virtual-environment
pipx install cijoe

# Print a list of bundled usage examples
cijoe --example

# Produce example script, config, and workflow
cijoe --example core.default

# Execute the workflow
cijoe cijoe-example-core.default/cijoe-workflow.yaml \
	--config cijoe-example-core.default/cijoe-config.toml

