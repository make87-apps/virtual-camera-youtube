const vscode = require('vscode');
const path = require('path');

function activate(context) {
  const workspaceRoot = '/home/state/code';
  const pipConfPath = path.join(workspaceRoot, 'pip.conf');
  const mainPyPath = path.join(workspaceRoot, 'app', 'main.py');

  vscode.workspace.openTextDocument(mainPyPath).then(document => {
    vscode.window.showTextDocument(document);

    const terminal = vscode.window.createTerminal('Setup Terminal');
    terminal.show(true);

    // 1) Activate the virtual environment
    terminal.sendText('source /home/state/venv/bin/activate');

    // 2) Conditionally export PIP_CONFIG_FILE if pip.conf exists
    terminal.sendText(`[ -f "${pipConfPath}" ] && export PIP_CONFIG_FILE="${pipConfPath}" && echo "Found pip.conf, using custom pip config" || echo "No pip.conf found, installing against default index"`);

    // 3) Install the package in editable mode
    terminal.sendText('pip install -e .');

    // Register terminal for disposal
    context.subscriptions.push(terminal);
  });
}

function deactivate() {}

exports.activate = activate;
exports.deactivate = deactivate;
