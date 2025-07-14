const vscode = require('vscode');

function activate(context) {
  vscode.workspace.openTextDocument('/home/state/code/src/main.rs').then(document => {
    vscode.window.showTextDocument(document);

    const terminal = vscode.window.createTerminal('Setup Terminal');
    terminal.show(true); // Show the terminal and make it visible
    terminal.sendText('cargo build');
  });
}

exports.activate = activate;
