const esbuild = require('esbuild');
const fs = require('node:fs');

const options = {
  entryPoints: ['src/extension.ts'],
  bundle: true,
  platform: 'node',
  target: 'node20',
  // jsonc-parser's UMD entry uses indirect require calls; bundle its ESM entry.
  mainFields: ['module', 'main'],
  external: ['vscode'],
  outfile: 'out/extension.js',
  sourcemap: true,
};

(async () => {
  if (process.argv.includes('--watch')) await (await esbuild.context(options)).watch();
  else await esbuild.build(options);
  fs.writeFileSync(
    'out/third-party-licenses.txt',
    ['yaml', 'jsonc-parser']
      .map((name) => {
        const directory = `node_modules/${name}`;
        const license = fs.readdirSync(directory).find((file) => /^LICENSE(?:\.md)?$/.test(file));
        return `${name}\n\n${fs.readFileSync(`${directory}/${license}`, 'utf8')}`;
      })
      .join('\n\n'),
  );
})().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
