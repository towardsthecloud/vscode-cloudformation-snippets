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
  targets: { label: string; url: string }[];
}

type Bindings = Record<string, string>;

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

function resolveName(value: unknown, bindings: Bindings): string {
  return String(value).replace(/\$\{([^}]+)\}|&\{([^}]+)\}/g, (match, dollar, ampersand) => {
    const name = dollar ?? ampersand;
    return Object.hasOwn(bindings, name) ? bindings[name] : match;
  });
}

function* expandedEntries(
  node: SyntaxNode | undefined,
  bindings: Bindings = {},
): Generator<{ key: SyntaxNode; value?: SyntaxNode; bindings: Bindings }> {
  for (const entry of node?.properties ?? []) {
    if (!String(entry.key.value).startsWith('Fn::ForEach::')) {
      yield { ...entry, bindings };
      continue;
    }
    const [identifier, collection, fragment] = entry.value?.items ?? [];
    if (typeof identifier?.value !== 'string' || !fragment) continue;
    if (!collection?.items) {
      // Preserve literal property names when a collection needs deployment-time evaluation.
      yield* expandedEntries(fragment, bindings);
      continue;
    }
    for (const item of collection.items) {
      if (typeof item.value === 'string') {
        yield* expandedEntries(fragment, { ...bindings, [identifier.value]: resolveName(item.value, bindings) });
      }
    }
  }
}

function indexLinks(content: string, language: string, data: Documentation): HoverLink[] {
  const root =
    language === 'yaml'
      ? fromYaml(parseDocument(content, { strict: false }).contents)
      : fromJson(parseTree(content, [], { allowTrailingComma: true }));
  const links = new Map<number, HoverLink>();
  const add = (node: SyntaxNode | undefined, url: string | undefined, label: string) => {
    if (node && url?.startsWith('https://docs.aws.amazon.com/')) {
      let link = links.get(node.start);
      if (!link) {
        link = { start: node.start, end: node.end, targets: [] };
        links.set(node.start, link);
      }
      if (!link.targets.some((target) => target.url === url)) link.targets.push({ label, url });
    }
  };
  const walk = (
    node: SyntaxNode | undefined,
    metadata: ResourceData | undefined,
    container?: 'List' | 'Map',
    bindings: Bindings = {},
  ) => {
    if (!node || !metadata) return;
    const conditional = property(node, 'Fn::If')?.value?.items ?? (node.tag === '!If' ? node.items : undefined);
    if (conditional) {
      for (const branch of conditional.slice(1, 3)) walk(branch, metadata, container, bindings);
      return;
    }
    if (container === 'Map') {
      for (const item of expandedEntries(node, bindings)) walk(item.value, metadata, undefined, item.bindings);
      return;
    }
    if (node.items) {
      for (const item of node.items) walk(item, metadata, undefined, bindings);
      return;
    }
    for (const entry of expandedEntries(node, bindings)) {
      const name = resolveName(entry.key.value, entry.bindings);
      const info = metadata.Properties[name];
      if (!info?.Docs) continue;
      add(entry.key, info.Docs, name);
      if (!info.Type) continue;
      const nested = data.PropertyTypes[info.Type];
      walk(entry.value, nested, info.Container, entry.bindings);
    }
  };
  for (const resource of expandedEntries(property(root, 'Resources')?.value)) {
    const type = property(resource.value, 'Type');
    const name = resolveName(type?.value?.value, resource.bindings);
    const metadata = data.Resources[name];
    if (!metadata?.Docs) continue;
    add(type?.key, metadata.Docs, name);
    add(type?.value, metadata.Docs, name);
    walk(property(resource.value, 'Properties')?.value, metadata, undefined, resource.bindings);
  }
  return [...links.values()].sort((left, right) => left.start - right.start);
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
          new vscode.MarkdownString(
            `Find documentation: ${link.targets.map((target) => `[${target.label}](${target.url})`).join('\n\n')}`,
          ),
          new vscode.Range(document.positionAt(link.start), document.positionAt(link.end)),
        );
      },
    }),
  );
}
