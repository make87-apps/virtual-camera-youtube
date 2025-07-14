#!/bin/bash

# Give permissions to use the /tmp directory. Required for pip package installs
sudo chmod 1777 /tmp

# Create make87 keys
ssh-keygen -t ed25519 -C "app@make87.com" -f "/root/.ssh/id_ed25519" -N ""

# copy over the mounted authorized_keys file to the root user's .ssh directory
if [ -f "/root/.ssh/authorized_keys_src" ]; then
  cp /root/.ssh/authorized_keys_src /root/.ssh/authorized_keys
  chown root:root /root/.ssh/authorized_keys
  chmod 600 /root/.ssh/authorized_keys
fi

# Start the SSH service
sudo service ssh start

# Set up Git config
git config --global user.email "make87"
git config --global user.name "todo@make87.com"

# Clone repository if GIT_URL is provided
TARGET_DIR="/home/state/code"

if [ -n "$GIT_URL" ]; then
    # Check if the target directory exists
    if [ ! -d "$TARGET_DIR" ]; then
        # Clone the repository if the directory does not exist
        git clone "$GIT_URL" "$TARGET_DIR"
        cd "$TARGET_DIR"

        # Checkout the specified branch if provided
        if [ -n "$GIT_BRANCH" ]; then
            git checkout "$GIT_BRANCH"
        fi
    else
        # Change to the target directory
        cd "$TARGET_DIR"

        # Ensure the correct remote URL is set with credentials
        git remote set-url origin "$GIT_URL"

        # Check if the specified branch is provided and switch if needed
        if [ -n "$GIT_BRANCH" ]; then
            CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
            if [ "$CURRENT_BRANCH" != "$GIT_BRANCH" ]; then
                # Stage and commit any changes in the current branch
                git add .
                git commit -m "Saving changes before switching branch" || echo "No changes to commit"

                # Push committed changes using the URL with credentials
                git push origin "$CURRENT_BRANCH" || echo "Failed to push changes"

                # Switch to the target branch
                git checkout "$GIT_BRANCH"
            fi
        fi

        # Pull the latest changes using the URL with credentials
        git pull origin "$GIT_BRANCH" || echo "Failed to pull latest changes"
    fi
fi


# if .vscode dir does not exit create it and add config files
# Path to the workspace
WORKSPACE_DIR="/home/state/code"

# Path to the .vscode directory
VSCODE_DIR="$WORKSPACE_DIR/.vscode"

PACKAGE_NAME=$(grep '^name =' /home/state/code/Cargo.toml | awk -F '"' '{print $2}')
# Check if .vscode directory exists; if not, create it and add config files
if [ ! -d "$VSCODE_DIR" ]; then
  echo "Creating .vscode directory and adding Rust configuration files..."
  mkdir -p "$VSCODE_DIR"

  # Create settings.json with Rust analyzer configurations
  cat <<EOF > "$VSCODE_DIR/settings.json"
{
    "rust-analyzer.serverPath": "/usr/local/cargo/bin/rust-analyzer",
    "rust-analyzer.checkOnSave.command": "clippy",
    "rust-analyzer.procMacro.enable": true,
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.organizeImports": true,
        "source.fixAll": true
    },
    "rustfmt.enableRangeFormatting": true,
    "rust-analyzer.cargo.runBuildScripts": true,
    "rust-analyzer.cargo.autoreload": true,
    "rust-analyzer.inlayHints.enable": true
}
EOF

  # Create launch.json to set up the debug configuration with LLDB
  cat <<EOF > "$VSCODE_DIR/launch.json"
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Debug Rust",
            "type": "lldb",
            "request": "launch",
            "program": "\${workspaceFolder}/target/debug/${PACKAGE_NAME}",
            "args": [],
            "cwd": "\${workspaceFolder}",
            "preLaunchTask": "cargo build",
            "stopOnEntry": false,
            "sourceLanguages": ["rust"]
        }
    ]
}
EOF

  # Optional: Create tasks.json for build tasks
  cat <<EOF > "$VSCODE_DIR/tasks.json"
{
    "version": "2.0.0",
    "tasks": [
        {
            "label": "cargo build",
            "type": "shell",
            "command": "cargo",
            "args": [
                "build"
            ],
            "group": {
                "kind": "build",
                "isDefault": true
            },
            "problemMatcher": [
                "\\$rustc"
            ]
        }
    ]
}
EOF

  echo ".vscode configuration for Rust has been set up."
fi

DEV_RUN_MODE=${DEV_RUN_MODE:-ide}
if [ "$DEV_RUN_MODE" = "ide" ]; then
    # Start OpenVSCode Server
    "$OPENVSCODE_SERVER_ROOT/bin/openvscode-server" --host=0.0.0.0 --port=3000 --without-connection-token --default-folder "$1"
elif [ "$DEV_RUN_MODE" = "ssh" ]; then
    # SSH server is already running. Keep the container running
    tail -f /dev/null
else
    # pip install, then run /home/state/code/app/main.py
    cd /home/state/code
    cargo build
    cargo run
fi