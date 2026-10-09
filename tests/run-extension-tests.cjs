const path = require('node:path');
const fs = require('node:fs');
const os = require('node:os');
const { runTests } = require('@vscode/test-electron');

fs.mkdirSync(path.resolve(__dirname, '../.vscode-test'), { recursive: true });
// Keep the profile path short enough for macOS's Unix socket limit.
const profile = fs.mkdtempSync(path.join(os.tmpdir(), 'vsc-'));
runTests({
  version: process.env.VSCODE_VERSION || '1.140.0',
  vscodeExecutablePath: process.env.VSCODE_EXECUTABLE_PATH,
  extensionDevelopmentPath: process.env.VSCODE_EXTENSION_ROOT || path.resolve(__dirname, '..'),
  extensionTestsPath: path.resolve(__dirname, 'extension.cjs'),
  launchArgs: [
    '--disable-extensions',
    '--skip-welcome',
    '--skip-release-notes',
    '--disable-workspace-trust',
    '--user-data-dir',
    profile,
  ],
})
  .catch((error) => {
    console.error(error);
    process.exitCode = 1;
  })
  .finally(() => {
    try {
      const logs = path.join(profile, 'logs');
      if (fs.existsSync(logs))
        fs.cpSync(logs, path.resolve(__dirname, '../.vscode-test/logs', process.env.VSCODE_VERSION || '1.140.0'), {
          recursive: true,
        });
    } finally {
      fs.rmSync(profile, { recursive: true, force: true });
    }
  });
