# Install cijoe into a pipx-managed virtual-environment
pipx install cijoe

# Print a list of bundled usage examples
cijoe --example

# Produce example script, config, and task
cijoe --example core.default

# Execute the task
cijoe cijoe-example-core.default/cijoe-task.yaml \
	--config cijoe-example-core.default/cijoe-config.toml

