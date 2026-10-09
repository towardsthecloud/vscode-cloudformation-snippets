const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vscode = require('vscode');
const { parse } = require('yaml');

const repo = path.resolve(__dirname, '..');

function hoverText(results) {
  return (results || [])
    .flatMap((result) => result.contents.map((item) => (typeof item === 'string' ? item : item.value)))
    .join('\n');
}

async function hover(language, content, needle) {
  const document = await vscode.workspace.openTextDocument({ language, content });
  const offset = content.indexOf(needle);
  assert.ok(offset >= 0, 'The hover target must occur in the fixture');
  const results = await vscode.commands.executeCommand(
    'vscode.executeHoverProvider',
    document.uri,
    document.positionAt(offset + 1),
  );
  return hoverText(results);
}

exports.run = async () => {
  const extension = vscode.extensions.getExtension('dannysteenman.cloudformation-yaml-snippets');
  assert.ok(extension, 'The development extension is installed');
  await extension.activate();
  const cases = [
    [
      'JSON and JSONC resource and numeric property documentation',
      async () => {
        const content = '{"Resources":{"Function":{"Properties":{"MemorySize":128},"Type":"AWS::Lambda::Function"}}}';
        assert.match(await hover('json', content, 'AWS::Lambda'), /aws-resource-lambda-function\.html/);
        assert.match(await hover('json', content, 'MemorySize'), /#cfn-lambda-function-memorysize/);
        const jsonc = content.replace('{"Resources"', '{// template comment\n"Resources"');
        assert.match(await hover('jsonc', jsonc, 'AWS::Lambda'), /aws-resource-lambda-function\.html/);
        assert.match(await hover('jsonc', jsonc, 'MemorySize'), /#cfn-lambda-function-memorysize/);
      },
    ],
    [
      'YAML comments, nested properties and intrinsic tags',
      async () => {
        const content =
          'Resources:\n  Function:\n    Type: AWS::Lambda::Function # inline comment\n    Properties:\n      MemorySize: 128\n      Environment:\n        Variables:\n          NAME: !Ref Name\n';
        assert.match(await hover('yaml', content, 'AWS::Lambda'), /aws-resource-lambda-function\.html/);
        assert.match(await hover('yaml', content, 'MemorySize'), /#cfn-lambda-function-memorysize/);
        assert.match(await hover('yaml', content, 'Variables'), /#cfn-lambda-function-environment-variables/);
        assert.doesNotMatch(await hover('yaml', content, 'NAME:'), /Find documentation/);
      },
    ],
    [
      'Conditional branches retain nested property documentation',
      async () => {
        const json =
          '{"Resources":{"Function":{"Type":"AWS::Lambda::Function","Properties":{"Environment":{"Fn::If":["UseEnv",{"Variables":{"NAME":"value"}},{"Ref":"AWS::NoValue"}]}}}}}';
        assert.match(await hover('json', json, 'Variables'), /#cfn-lambda-function-environment-variables/);
        const yaml =
          'Resources:\n  Function:\n    Type: AWS::Lambda::Function\n    Properties:\n      Environment: !If\n        - UseEnv\n        - Variables:\n            NAME: value\n        - !Ref AWS::NoValue\n';
        assert.match(await hover('yaml', yaml, 'Variables'), /#cfn-lambda-function-environment-variables/);
      },
    ],
    [
      'ForEach resource fragments retain documentation through nested loops',
      async () => {
        const json =
          // biome-ignore lint/suspicious/noTemplateCurlyInString: CloudFormation uses literal substitution placeholders.
          '{"Transform":"AWS::LanguageExtensions","Resources":{"Fn::ForEach::Regions":["Region",["eu-west-1"],{"Fn::ForEach::Functions":["Name",["Worker"],{"Function${Region}${Name}":{"Type":"AWS::Lambda::Function","Properties":{"MemorySize":128,"Environment":{"Variables":{"NAME":"value"}}}}}]}]}}';
        assert.match(await hover('json', json, 'AWS::Lambda'), /aws-resource-lambda-function\.html/);
        assert.match(await hover('json', json, 'MemorySize'), /#cfn-lambda-function-memorysize/);
        assert.match(await hover('json', json, 'Variables'), /#cfn-lambda-function-environment-variables/);
        const yaml =
          // biome-ignore lint/suspicious/noTemplateCurlyInString: CloudFormation uses literal substitution placeholders.
          'Transform: AWS::LanguageExtensions\nResources:\n  Fn::ForEach::Functions:\n    - Name\n    - [Worker]\n    - Function${Name}:\n        Type: AWS::Lambda::Function\n        Properties:\n          MemorySize: 128\n          Environment:\n            Variables:\n              NAME: value\n';
        assert.match(await hover('yaml', yaml, 'AWS::Lambda'), /aws-resource-lambda-function\.html/);
        assert.match(await hover('yaml', yaml, 'MemorySize'), /#cfn-lambda-function-memorysize/);
        assert.match(await hover('yaml', yaml, 'Variables'), /#cfn-lambda-function-environment-variables/);
      },
    ],
    [
      'Hovers stay inside resource boundaries and property keys',
      async () => {
        const content =
          'Resources:\n  Bucket:\n    Type: AWS::S3::Bucket\n  Policy:\n    Properties:\n      BucketName: value\n    Type: AWS::S3::BucketPolicy\nOutputs:\n  BucketName:\n    Value: string\n';
        assert.doesNotMatch(await hover('yaml', content, 'BucketName: value'), /Find documentation/);
        assert.doesNotMatch(await hover('yaml', content, 'BucketName:\n'), /Find documentation/);
        assert.doesNotMatch(await hover('yaml', content, 'value'), /Find documentation/);
      },
    ],
    [
      'Document edits invalidate hover results',
      async () => {
        const document = await vscode.workspace.openTextDocument({
          language: 'yaml',
          content: 'Resources:\n  Resource:\n    Type: AWS::S3::Bucket\n    Properties:\n      BucketName: name\n',
        });
        const position = new vscode.Position(4, 7);
        const before = await vscode.commands.executeCommand('vscode.executeHoverProvider', document.uri, position);
        assert.match(hoverText(before), /cfn-s3-bucket-bucketname/);
        const edit = new vscode.WorkspaceEdit();
        edit.replace(document.uri, new vscode.Range(2, 10, 2, 25), 'AWS::S3::BucketPolicy');
        assert.ok(await vscode.workspace.applyEdit(edit));
        const after = await vscode.commands.executeCommand('vscode.executeHoverProvider', document.uri, position);
        assert.doesNotMatch(hoverText(after), /Find documentation/);
      },
    ],
    [
      'Generated JSON and YAML snippets insert with valid scalar and object defaults',
      async () => {
        const snippets = JSON.parse(
          fs.readFileSync(path.join(extension.extensionPath, 'snippets/json-cfn-resource-types.json'), 'utf8'),
        );
        const document = await vscode.workspace.openTextDocument({ language: 'json', content: '{}' });
        const editor = await vscode.window.showTextDocument(document);
        for (const resource of ['AWS::Lambda::Function', 'AWS::IAM::Role', 'AWS::S3::Bucket']) {
          const text = `{${snippets[resource].body.join('\n')}}`;
          await editor.insertSnippet(new vscode.SnippetString(text), new vscode.Range(0, 0, document.lineCount, 0));
          const inserted = JSON.parse(document.getText()).LogicalID;
          assert.equal(inserted.Type, resource);
          if (resource === 'AWS::Lambda::Function') {
            assert.deepEqual(inserted.Properties.Architectures, ['String']);
            assert.equal(inserted.Properties.MemorySize, 0);
            assert.deepEqual(inserted.Properties.Environment.Variables, { Key: 'String' });
          }
          if (resource === 'AWS::IAM::Role') assert.deepEqual(inserted.Properties.AssumeRolePolicyDocument, {});
        }
        const yamlSnippets = JSON.parse(
          fs.readFileSync(path.join(extension.extensionPath, 'snippets/yaml-cfn-resource-types.json'), 'utf8'),
        );
        const yamlDocument = await vscode.workspace.openTextDocument({ language: 'yaml', content: '' });
        const yamlEditor = await vscode.window.showTextDocument(yamlDocument);
        await yamlEditor.insertSnippet(new vscode.SnippetString(yamlSnippets['AWS::Lambda::Function'].body.join('\n')));
        const insertedYaml = parse(yamlDocument.getText()).LogicalID;
        assert.equal(insertedYaml.Type, 'AWS::Lambda::Function');
        assert.deepEqual(insertedYaml.Properties.Architectures, ['String']);
        assert.equal(insertedYaml.Properties.MemorySize, 0);
        assert.deepEqual(insertedYaml.Properties.Environment.Variables, { Key: 'String' });
      },
    ],
  ];
  const results = [];
  for (const [name, run] of cases) {
    try {
      await run();
      results.push({ name, status: 'passed' });
      console.log(`PASS ${name}`);
    } catch (error) {
      results.push({ name, status: 'failed', error: String(error.stack || error) });
      console.error(`FAIL ${name}: ${error}`);
    }
  }
  fs.mkdirSync(path.join(repo, '.vscode-test'), { recursive: true });
  fs.writeFileSync(
    path.join(repo, `.vscode-test/extension-test-results-${vscode.version}.json`),
    JSON.stringify({ vscode: vscode.version, results }, null, 2),
  );
  assert.equal(results.filter((result) => result.status === 'failed').length, 0, 'Extension Host regressions failed');
};
