import { type Node as JsonNode, parseTree } from 'jsonc-parser';
import * as vscode from 'vscode';
import { isMap, isNode, isScalar, isSeq, parseDocument } from 'yaml';

interface SyntaxNode {
  start: number;
  end: number;
  value?: unknown;
  tag?: string;
  properties?: { key: SyntaxNode; value?: SyntaxNode }[];
  items?: SyntaxNode[];
}

interface PropertyData {
  Docs: string;
  Type?: string;
  Container?: 'List' | 'Map';
}

interface ResourceData {
  Docs?: string;
  Properties: Record<string, PropertyData>;
}

interface Documentation {
  Resources: Record<string, ResourceData>;
  PropertyTypes: Record<string, ResourceData>;
}

interface HoverLink {
  start: number;
  end: number;
  url: string;
}

function fromJson(node: JsonNode | undefined): SyntaxNode | undefined {
  if (!node) return undefined;
  const result: SyntaxNode = { start: node.offset, end: node.offset + node.length, value: node.value };
  if (node.type === 'object') {
    result.properties = (node.children ?? []).flatMap((property) => {
      const key = fromJson(property.children?.[0]);
      return key ? [{ key, value: fromJson(property.children?.[1]) }] : [];
    });
  } else if (node.type === 'array') {
    result.items = (node.children ?? []).flatMap((item) => {
      const value = fromJson(item);
      return value ? [value] : [];
    });
  }
  return result;
}

function fromYaml(node: unknown): SyntaxNode | undefined {
  if (!isNode(node) || !node.range) return undefined;
  const result: SyntaxNode = { start: node.range[0], end: node.range[1], tag: node.tag };
  if (isScalar(node)) result.value = node.value;
  else if (isMap(node)) {
    result.properties = node.items.flatMap((pair) => {
      const key = fromYaml(pair.key);
      return key ? [{ key, value: fromYaml(pair.value) }] : [];
    });
  } else if (isSeq(node)) {
    result.items = node.items.flatMap((item) => {
      const value = fromYaml(item);
      return value ? [value] : [];
    });
  }
  return result;
}

function property(node: SyntaxNode | undefined, name: string) {
  return node?.properties?.find((entry) => entry.key.value === name);
}

function indexLinks(content: string, language: string, data: Documentation): HoverLink[] {
  const root =
    language === 'yaml'
      ? fromYaml(parseDocument(content, { strict: false }).contents)
      : fromJson(parseTree(content, [], { allowTrailingComma: true }));
  const links: HoverLink[] = [];
  const add = (node: SyntaxNode | undefined, url: string | undefined) => {
    if (node && url?.startsWith('https://docs.aws.amazon.com/')) {
      links.push({ start: node.start, end: node.end, url });
    }
  };
  const walk = (node: SyntaxNode | undefined, metadata: ResourceData | undefined, container?: 'List' | 'Map') => {
    if (!node || !metadata) return;
    const conditional = property(node, 'Fn::If')?.value?.items ?? (node.tag === '!If' ? node.items : undefined);
    if (conditional) {
      for (const branch of conditional.slice(1, 3)) walk(branch, metadata, container);
      return;
    }
    if (container === 'Map') {
      for (const item of node.properties ?? []) walk(item.value, metadata);
      return;
    }
    if (node.items) {
      for (const item of node.items) walk(item, metadata);
      return;
    }
    for (const entry of node.properties ?? []) {
      const info = metadata.Properties[String(entry.key.value)];
      if (!info?.Docs) continue;
      add(entry.key, info.Docs);
      if (!info.Type) continue;
      const nested = data.PropertyTypes[info.Type];
      walk(entry.value, nested, info.Container);
    }
  };
  for (const resource of property(root, 'Resources')?.value?.properties ?? []) {
    const type = property(resource.value, 'Type');
    const metadata = data.Resources[String(type?.value?.value)];
    if (!metadata?.Docs) continue;
    add(type?.key, metadata.Docs);
    add(type?.value, metadata.Docs);
    walk(property(resource.value, 'Properties')?.value, metadata);
  }
  return links.sort((left, right) => left.start - right.start);
}

export function activate(context: vscode.ExtensionContext) {
  const output = vscode.window.createOutputChannel('CloudFormation Snippets');
  context.subscriptions.push(output);
  let loading: Promise<Documentation | null> | undefined;
  const loadDocumentation = () => {
    loading ??= (async () => {
      try {
        const bytes = await vscode.workspace.fs.readFile(
          vscode.Uri.joinPath(context.extensionUri, 'snippets', 'raw-cfn-resources-output.json'),
        );
        const data: Documentation = JSON.parse(new TextDecoder().decode(bytes));
        if (!data.Resources || !data.PropertyTypes) throw new Error('Invalid documentation index');
        output.appendLine(`Loaded documentation for ${Object.keys(data.Resources).length} resources`);
        return data;
      } catch {
        output.appendLine('Unable to load documentation. Snippets remain available.');
        return null;
      }
    })();
    return loading;
  };
  const cache = new Map<string, { version: number; links: HoverLink[] }>();
  context.subscriptions.push(
    vscode.workspace.onDidCloseTextDocument((document) => cache.delete(document.uri.toString())),
    new vscode.Disposable(() => cache.clear()),
    vscode.languages.registerHoverProvider(['yaml', 'json', 'jsonc'], {
      async provideHover(document, position, token) {
        if (token.isCancellationRequested) return null;
        const key = document.uri.toString();
        let entry = cache.get(key);
        if (entry?.version !== document.version) {
          const version = document.version;
          const content = document.getText();
          if (!content.includes('AWS::') || !content.includes('Resources')) {
            cache.set(key, { version, links: [] });
            return null;
          }
          const data = await loadDocumentation();
          if (!data || token.isCancellationRequested || document.version !== version || document.isClosed) return null;
          try {
            entry = { version, links: indexLinks(content, document.languageId, data) };
          } catch {
            entry = { version: document.version, links: [] };
          }
          cache.set(key, entry);
        }
        const offset = document.offsetAt(position);
        let low = 0;
        let high = entry.links.length;
        while (low < high) {
          const middle = Math.floor((low + high) / 2);
          if (entry.links[middle].start <= offset) low = middle + 1;
          else high = middle;
        }
        const link = entry.links[low - 1];
        if (!link || offset >= link.end || token.isCancellationRequested) return null;
        return new vscode.Hover(
          new vscode.MarkdownString(`Find documentation: [AWS documentation](${link.url})`),
          new vscode.Range(document.positionAt(link.start), document.positionAt(link.end)),
        );
      },
    }),
  );
}
