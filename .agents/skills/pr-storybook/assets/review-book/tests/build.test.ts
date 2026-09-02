import assert from 'node:assert/strict'
import {spawnSync} from 'node:child_process'
import {mkdir, mkdtemp, readFile, readdir, rm, writeFile} from 'node:fs/promises'
import path from 'node:path'
import {tmpdir} from 'node:os'
import test from 'node:test'
import {
  buildReviewBook,
  parseArguments,
  pullRequestDiffTarget,
  pullRequestUrl,
  readBook,
  readSidecar,
  safeLink,
  selectEvidence,
  validateReviewBook,
} from '../src/build.js'

const runId = `sha256:${'1'.repeat(64)}`
const hunkId = `unit:${'a'.repeat(64)}`
const metadataId = `unit:${'b'.repeat(64)}`
const fileId = `file:${'c'.repeat(64)}`
const metadataFileId = `file:${'d'.repeat(64)}`
const runtimeRoot = path.resolve(import.meta.dirname, '..')

const hunk = {
  id: hunkId,
  kind: 'hunk' as const,
  header: '@@ -1 +1 @@',
  oldRange: {start: 1, count: 1},
  newRange: {start: 1, count: 1},
  lines: [
    {kind: 'deletion' as const, oldLine: 1, newLine: null, text: 'old value'},
    {kind: 'addition' as const, oldLine: null, newLine: 1, text: 'new value'},
  ],
}

function defaultMdx(): string {
  return `# Understand the change

## Change the behavior

The new value replaces the old value.

\`\`\`json
{"before":"old value","after":"new value"}
\`\`\`

<Diff ref="${hunkId}@0:2" />

<Finding id="unsafe-value" />

## Update the asset

<Diff ref="${metadataId}" />
`
}

function defaultCoverage() {
  return [
    {unitId: hunkId, section: 'Change the behavior', disposition: 'displayed'},
    {unitId: metadataId, section: 'Update the asset', disposition: 'displayed'},
  ]
}

async function writeBundle(options: {
  mdx?: string
  coverage?: unknown[]
  findings?: unknown[]
  book?: Record<string, unknown>
  url?: string
} = {}): Promise<{root: string; bundle: string; output: string}> {
  const root = await mkdtemp(path.join(tmpdir(), 'review-book-'))
  const bundle = path.join(root, 'bundle')
  const output = path.join(bundle, 'site')
  await mkdir(path.join(bundle, 'chapters'), {recursive: true})
  await writeFile(path.join(bundle, 'book.json'), JSON.stringify(options.book ?? {
    schemaVersion: 1,
    runId,
    title: 'A general review book',
  }))
  await writeFile(path.join(bundle, 'run.json'), JSON.stringify({
    schemaVersion: 1,
    runId,
    createdAt: '2026-09-01T00:00:00Z',
    subject: {
      repository: 'example/project',
      title: 'Change one value',
      url: options.url ?? 'https://github.com/example/project/pull/42',
      base: '7'.repeat(40),
      head: '3'.repeat(40),
      mergeBase: '2'.repeat(40),
      patchSha256: `sha256:${'4'.repeat(64)}`,
    },
    files: [
      {
        id: fileId,
        path: 'src/value.ts',
        oldPath: null,
        status: 'modified',
        isBinary: false,
        patchSha256: `sha256:${'5'.repeat(64)}`,
        additions: 1,
        deletions: 1,
        units: [hunk],
      },
      {
        id: metadataFileId,
        path: 'public/diagram.png',
        oldPath: null,
        status: 'modified',
        isBinary: true,
        patchSha256: `sha256:${'6'.repeat(64)}`,
        additions: 0,
        deletions: 0,
        units: [{id: metadataId, kind: 'metadata', label: 'Binary change'}],
      },
    ],
    totals: {files: 2, units: 2, additions: 1, deletions: 1},
  }))
  await writeFile(path.join(bundle, 'findings.json'), JSON.stringify({
    schemaVersion: 2,
    runId,
    findings: options.findings ?? [{
      id: 'unsafe-value',
      status: 'verified',
      severity: 'P2',
      title: 'Validate the new value',
      summary: 'The new value has no validation.',
      trigger: 'The caller supplies an invalid value.',
      impact: 'An invalid value can enter the system.',
      fix: 'Validate the value before you store it.',
      anchors: [{fileId, unitId: hunkId, side: 'new', line: 1}],
    }],
  }))
  await writeFile(path.join(bundle, 'chapters', '01-understand.evidence.json'), JSON.stringify({
    schemaVersion: 1,
    runId,
    chapter: '01-understand',
    coverage: options.coverage ?? defaultCoverage(),
  }))
  await writeFile(path.join(bundle, 'chapters', '01-understand.mdx'), options.mdx ?? defaultMdx())
  return {root, bundle, output}
}

async function withBundle(
  options: Parameters<typeof writeBundle>[0],
  action: (fixture: Awaited<ReturnType<typeof writeBundle>>) => Promise<void>,
): Promise<void> {
  const fixture = await writeBundle(options)
  try {
    await action(fixture)
  } finally {
    await rm(fixture.root, {recursive: true, force: true})
  }
}

test('builds static chapter pages from a reusable bundle', async () => {
  await withBundle({}, async ({bundle, output}) => {
    await buildReviewBook({bundle, output})
    const html = await readFile(path.join(output, 'index.html'), 'utf8')
    const chapterHtml = await readFile(path.join(output, '01-understand.html'), 'utf8')
    const standaloneHtml = await readFile(path.join(output, 'standalone.html'), 'utf8')
    const css = await readFile(path.join(output, 'assets', 'book.css'), 'utf8')
    const head = '3'.repeat(40)

    assert.match(html, /Understand the change/)
    assert.match(html, new RegExp(`example/project · ${'2'.repeat(10)} → ${'3'.repeat(10)}`))
    assert.match(html, /finding-unsafe-value/)
    assert.match(html, /<strong>Trigger:<\/strong> The caller supplies an invalid value\./)
    assert.equal(chapterHtml, html)
    assert.match(html, /evidence-[a-f0-9]{64}-0-2-new-1/)
    assert.match(html, /aria-label="Binary change: public\/diagram\.png"/)
    assert.match(html, new RegExp(`href="https://github\\.com/example/project/blob/${head}/src/value\\.ts#L1"`))
    assert.match(html, new RegExp(`href="https://github\\.com/example/project/blob/${head}/public/diagram\\.png"`))
    assert.match(html, new RegExp(`class="finding-link" href="https://github\\.com/example/project/blob/${head}/src/value\\.ts#L1"`))
    assert.match(html, /<details class="mobile-chapters">/)
    assert.match(html, /<aside class="book-sidebar">/)
    assert.match(html, /<main class="book-main">/)
    assert.match(html, /<h1 id="chapter" tabindex="-1">Understand the change<\/h1>/)
    assert.doesNotMatch(html, /<main[^>]+id="chapter"/)
    assert.match(html, /<aside class="finding"/)
    assert.match(html, /<nav class="chapter-nav" aria-label="Chapters"><p class="chapter-nav-label">Chapters<\/p>/)
    const headings = html.match(/<h[1-6]\b[^>]*>[^<]*/g) ?? []
    assert.match(headings[0] ?? '', /^<h1\b[^>]*>Understand the change$/)
    assert.equal(headings.some((heading) => />Chapters$/.test(heading)), false)
    assert.equal(headings.some((heading) => /Validate the new value/.test(heading)), false)
    assert.match(html, /href="\.\/01-understand\.html#chapter"/)
    assert.match(html, /href="\.\/assets\/book\.css\?v=[a-f0-9]{12}"/)
    assert.doesNotMatch(html, /<script\b/i)
    assert.doesNotMatch(html, /<(?:link|img|script)[^>]+(?:href|src)="https?:/i)
    assert.match(standaloneHtml, /<style>:root \{/)
    assert.match(standaloneHtml, /id="chapter-01-understand"/)
    assert.match(standaloneHtml, /href="#chapter-01-understand"/)
    assert.doesNotMatch(standaloneHtml, /<link\b/i)
    assert.doesNotMatch(standaloneHtml, /<script\b/i)
    assert.doesNotMatch(html, /<figcaption[^>]*>[^<]*(?:Example|json)/i)
    assert.match(css, /color-scheme: dark/)
    assert.doesNotMatch(css, /prefers-color-scheme/)
  })
})

test('the documented Node entry point accepts bundle and output arguments', async () => {
  await withBundle({}, async ({root, bundle, output}) => {
    const result = spawnSync(process.execPath, [path.join(runtimeRoot, 'build.mjs'), '--bundle', bundle, '--output', output], {
      cwd: root,
      encoding: 'utf8',
    })
    assert.equal(result.status, 0, result.stderr)
    assert.match(result.stdout, /Built PR Storybook in/)
    assert.match(await readFile(path.join(output, 'index.html'), 'utf8'), /A general review book/)
    assert.match(await readFile(path.join(output, 'standalone.html'), 'utf8'), /A general review book/)
  })
})

test('validate-only runs the complete bundle checks without creating a site', async () => {
  await withBundle({}, async ({root, bundle, output}) => {
    await validateReviewBook({bundle})
    await assert.rejects(readFile(path.join(output, 'index.html')))

    const result = spawnSync(process.execPath, [path.join(runtimeRoot, 'build.mjs'), '--bundle', bundle, '--validate-only'], {
      cwd: root,
      encoding: 'utf8',
    })
    assert.equal(result.status, 0, result.stderr)
    assert.match(result.stdout, /Validated PR Storybook bundle/)
    await assert.rejects(readFile(path.join(output, 'index.html')))
  })
})

test('unsupported HTTPS change URLs omit direct repository links', async () => {
  await withBundle({url: 'https://review.example.test/changes/42'}, async ({bundle, output}) => {
    await buildReviewBook({bundle, output})
    const html = await readFile(path.join(output, 'index.html'), 'utf8')
    assert.doesNotMatch(html, /class="code-path" href=/)
    assert.match(html, /<span class="code-path">src\/value\.ts<\/span>/)
    assert.match(html, new RegExp(`class="finding-link" href="#evidence-${hunkId.slice(5)}-0-2-new-1"`))
  })
})

test('GitHub Enterprise pull URLs produce immutable evidence links', async () => {
  await withBundle({url: 'https://github.enterprise.test/example/project/pull/42'}, async ({bundle, output}) => {
    await buildReviewBook({bundle, output})
    const html = await readFile(path.join(output, 'index.html'), 'utf8')
    assert.match(html, new RegExp(`class="finding-link" href="https://github\\.enterprise\\.test/example/project/blob/${'3'.repeat(40)}/src/value\\.ts#L1"`))
  })
})

test('publishes through a nonpredictable stage and preserves the old site on validation failure', async () => {
  await withBundle({}, async ({bundle, output}) => {
    await mkdir(output)
    const oldPage = path.join(output, 'index.html')
    await writeFile(oldPage, 'old site')
    const predictableStage = `${output}.stage-${process.pid}`
    await mkdir(predictableStage)
    const sentinel = path.join(predictableStage, 'keep.txt')
    await writeFile(sentinel, 'keep')

    await buildReviewBook({bundle, output})
    assert.match(await readFile(oldPage, 'utf8'), /A general review book/)
    assert.equal(await readFile(sentinel, 'utf8'), 'keep')
    assert.equal((await readdir(bundle)).some((name) => name.startsWith('.pr-storybook-stage-')), false)

    await writeFile(path.join(bundle, 'chapters', '01-understand.mdx'), '# Broken\n\n{process.exit(1)}\n')
    await assert.rejects(buildReviewBook({bundle, output}), /not allowed/)
    assert.match(await readFile(oldPage, 'utf8'), /A general review book/)
  })
})

test('permits several small excerpts for one displayed owner', async () => {
  const mdx = `# Understand the change

## Change the behavior

<Diff ref="${hunkId}@0:2" />

<Finding id="unsafe-value" />

<Diff ref="${hunkId}@1:1" />

## Update the asset

The binary change supports the release.
`
  const coverage = [
    {unitId: hunkId, section: 'Change the behavior', disposition: 'displayed'},
    {unitId: metadataId, section: 'Update the asset', disposition: 'supporting', reason: 'The image supports the changed screen.'},
  ]
  await withBundle({mdx, coverage}, async ({bundle, output}) => {
    await buildReviewBook({bundle, output})
    const html = await readFile(path.join(output, 'index.html'), 'utf8')
    assert.match(html, new RegExp(`${hunkId.slice(5)}-0-2`, 'g'))
    assert.match(html, new RegExp(`${hunkId.slice(5)}-1-1`, 'g'))
  })
})

for (const [name, source, pattern] of [
  ['import', 'import value from "./bad.js"\n\n# Test', /not allowed/],
  ['export', 'export const value = 1\n\n# Test', /not allowed/],
  ['flow expression', '# Test\n\n{process.exit(1)}', /not allowed/],
  ['inline expression', '# Test\n\nText {process.exit(1)}', /not allowed/],
  ['raw HTML', '# Test\n\n<script>alert(1)</script>', /not allowed/],
  ['unknown component', '# Test\n\n<Widget />', /not allowed/],
  ['expression property', '# Test\n\n<Finding id={process.exit(1)} />', /literal/],
  ['unsafe link', '# Test\n\n[bad](javascript:alert(1))', /link target/],
  ['current-directory link', '# Test\n\n[bad](./local.html)', /link target/],
  ['parent-directory link', '# Test\n\n[bad](../parent.html)', /link target/],
] as const) {
  test(`rejects ${name}`, async () => {
    await withBundle({mdx: source}, async ({bundle, output}) => {
      await assert.rejects(buildReviewBook({bundle, output}), pattern)
    })
  })
}

test('requires a displayed unit in its assigned heading section', async () => {
  const coverage = [
    {unitId: hunkId, section: 'Wrong section', disposition: 'displayed'},
    {unitId: metadataId, section: 'Update the asset', disposition: 'displayed'},
  ]
  await withBundle({coverage}, async ({bundle, output}) => {
    await assert.rejects(buildReviewBook({bundle, output}), /not its assigned section Wrong section/)
  })
})

test('requires a short reason for supporting and mechanical units', () => {
  assert.throws(() => readSidecar({
    schemaVersion: 1,
    runId,
    chapter: '01-test',
    coverage: [{unitId: hunkId, section: 'Test', disposition: 'mechanical'}],
  }, 'sidecar', runId), /needs exactly these keys/)
})

test('requires a hunk range and forbids a metadata range', async () => {
  const noHunkRange = defaultMdx().replace(`${hunkId}@0:2`, hunkId)
  await withBundle({mdx: noHunkRange}, async ({bundle, output}) => {
    await assert.rejects(buildReviewBook({bundle, output}), /hunk Diff ref needs/)
  })
  const metadataRange = defaultMdx().replace(metadataId, `${metadataId}@0:1`)
  await withBundle({mdx: metadataRange}, async ({bundle, output}) => {
    await assert.rejects(buildReviewBook({bundle, output}), /metadata Diff ref cannot/)
  })
})

test('allows findings after anchored evidence in the same section', async () => {
  const separated = defaultMdx().replace(
    '<Finding id="unsafe-value" />',
    'More explanation.\n\n<Finding id="unsafe-value" />',
  )
  await withBundle({mdx: separated}, async ({bundle, output}) => {
    await buildReviewBook({bundle, output})
    assert.match(await readFile(path.join(output, 'index.html'), 'utf8'), /finding-unsafe-value/)
  })

  const wrongSection = defaultMdx().replace(
    '<Finding id="unsafe-value" />',
    '## A different section\n\n<Finding id="unsafe-value" />',
  )
  await withBundle({mdx: wrongSection}, async ({bundle, output}) => {
    await assert.rejects(buildReviewBook({bundle, output}), /must follow a Diff in section A different section/)
  })

  const wrongAnchor = [{
    id: 'unsafe-value',
    status: 'verified',
    severity: 'P2',
    title: 'Validate the new value',
    summary: 'The new value has no validation.',
    trigger: 'The caller supplies an invalid value.',
    impact: 'An invalid value can enter the system.',
    fix: 'Validate the value before you store it.',
    anchors: [{fileId, unitId: hunkId, side: 'new', line: 99}],
  }]
  await withBundle({findings: wrongAnchor}, async ({bundle, output}) => {
    await assert.rejects(buildReviewBook({bundle, output}), /contains its changed-line anchor/)
  })
})

test('allows two findings to use one earlier excerpt', async () => {
  const findings = [
    {
      id: 'unsafe-value',
      status: 'verified',
      severity: 'P2',
      title: 'Validate the new value',
      summary: 'The new value has no validation.',
      trigger: 'The caller supplies an invalid value.',
      impact: 'An invalid value can enter the system.',
      fix: 'Validate the value before you store it.',
      anchors: [{fileId, unitId: hunkId, side: 'new', line: 1}],
    },
    {
      id: 'audit-value',
      status: 'verified',
      severity: 'P3',
      title: 'Record the new value',
      summary: 'The change does not record the new value.',
      trigger: 'The caller changes the value.',
      impact: 'An operator cannot trace the change.',
      fix: 'Record the accepted value.',
      anchors: [{fileId, unitId: hunkId, side: 'new', line: 1}],
    },
  ]
  const mdx = defaultMdx().replace(
    '<Finding id="unsafe-value" />',
    'The evidence supports both findings.\n\n<Finding id="unsafe-value" />\n\n<Finding id="audit-value" />',
  )
  await withBundle({mdx, findings}, async ({bundle, output}) => {
    await buildReviewBook({bundle, output})
    const html = await readFile(path.join(output, 'index.html'), 'utf8')
    assert.match(html, /finding-unsafe-value/)
    assert.match(html, /finding-audit-value/)
    assert.equal((html.match(/class="evidence-block"/g) ?? []).length, 1)
  })
})

test('old-side hunk findings link to the exact merge-base line', async () => {
  const findings = [{
    id: 'old-value-risk',
    status: 'verified',
    severity: 'P2',
    title: 'Keep the old behavior available',
    summary: 'The change removes the old value.',
    trigger: 'A caller still needs the old value.',
    impact: 'The caller can fail after the update.',
    fix: 'Keep a compatibility path.',
    anchors: [{fileId, unitId: hunkId, side: 'old', line: 1}],
  }]
  const mdx = defaultMdx().replace('unsafe-value', 'old-value-risk')
  await withBundle({mdx, findings}, async ({bundle, output}) => {
    await buildReviewBook({bundle, output})
    const html = await readFile(path.join(output, 'index.html'), 'utf8')
    assert.match(html, new RegExp(`class="finding-link" href="https://github\\.com/example/project/blob/${'2'.repeat(40)}/src/value\\.ts#L1"`))
  })
})

test('requires each review unit and verified finding exactly once', async () => {
  await withBundle({coverage: [defaultCoverage()[0]]}, async ({bundle, output}) => {
    await assert.rejects(buildReviewBook({bundle, output}), /outside this chapter coverage|not assigned/)
  })

  const duplicateFinding = defaultMdx().replace(
    '## Update the asset',
    `<Diff ref="${hunkId}@1:1" />\n\n<Finding id="unsafe-value" />\n\n## Update the asset`,
  )
  await withBundle({mdx: duplicateFinding}, async ({bundle, output}) => {
    await assert.rejects(buildReviewBook({bundle, output}), /finding unsafe-value is repeated/)
  })
})

test('validates the minimal book contract and command line', () => {
  assert.deepEqual(readBook({schemaVersion: 1, runId, title: 'Review'}), {schemaVersion: 1, runId, title: 'Review'})
  assert.throws(() => readBook({schemaVersion: 1, runId, title: 'Review', repository: 'extra'}), /exactly these keys/)
  assert.throws(() => readBook({schemaVersion: 1, runId, title: 'Unsafe \u202e title'}), /bidirectional controls/)
  assert.deepEqual(parseArguments(['--bundle', './bundle', '--output', './dist']), {
    bundle: path.resolve('./bundle'),
    output: path.resolve('./dist'),
    validateOnly: false,
  })
  assert.deepEqual(parseArguments(['--bundle', './bundle', '--validate-only']), {
    bundle: path.resolve('./bundle'),
    output: null,
    validateOnly: true,
  })
  assert.throws(() => parseArguments(['--bundle', './bundle']), /usage/)
  assert.throws(() => parseArguments(['--bundle', './bundle', '--validate-only', '--output', './dist']), /usage/)
})

test('binds every chapter sidecar to the frozen run', () => {
  assert.throws(() => readSidecar({
    schemaVersion: 1,
    chapter: '01-test',
    coverage: [],
  }, 'sidecar', runId), /exactly these keys/)
  assert.throws(() => readSidecar({
    schemaVersion: 1,
    runId: `sha256:${'9'.repeat(64)}`,
    chapter: '01-test',
    coverage: [],
  }, 'sidecar', runId), /does not match book.json/)
  assert.throws(() => readSidecar({
    schemaVersion: 1,
    runId: 'not-a-digest',
    chapter: '01-test',
    coverage: [],
  }, 'sidecar', runId), /lowercase SHA-256 ID/)
})

test('refuses to replace any directory except bundle site', async () => {
  await withBundle({}, async ({root, bundle}) => {
    const unsafeOutput = path.join(root, 'other')
    await mkdir(unsafeOutput)
    const sentinel = path.join(unsafeOutput, 'keep.txt')
    await writeFile(sentinel, 'keep')
    await assert.rejects(
      buildReviewBook({bundle, output: unsafeOutput}),
      /output must equal the bundle site directory/,
    )
    assert.equal(await readFile(sentinel, 'utf8'), 'keep')
  })
})

test('rejects headings below H3', async () => {
  await withBundle({mdx: '# Test\n\n#### Too deep\n'}, async ({bundle, output}) => {
    await assert.rejects(buildReviewBook({bundle, output}), /heading depth must be H1, H2, or H3/)
  })
})

test('adds main-region fragments to next and previous chapter links', async () => {
  await withBundle({}, async ({bundle, output}) => {
    await writeFile(path.join(bundle, 'chapters', '01-understand.evidence.json'), JSON.stringify({
      schemaVersion: 1,
      runId,
      chapter: '01-understand',
      coverage: [{unitId: hunkId, section: 'Change the behavior', disposition: 'displayed'}],
    }))
    await writeFile(path.join(bundle, 'chapters', '01-understand.mdx'), `# Understand the change

## Change the behavior

<Diff ref="${hunkId}@0:2" />

<Finding id="unsafe-value" />
`)
    await writeFile(path.join(bundle, 'chapters', '02-assets.evidence.json'), JSON.stringify({
      schemaVersion: 1,
      runId,
      chapter: '02-assets',
      coverage: [{unitId: metadataId, section: 'Update the asset', disposition: 'displayed'}],
    }))
    await writeFile(path.join(bundle, 'chapters', '02-assets.mdx'), `# Inspect the assets

## Update the asset

<Diff ref="${metadataId}" />
`)
    await buildReviewBook({bundle, output})
    const first = await readFile(path.join(output, '01-understand.html'), 'utf8')
    const second = await readFile(path.join(output, '02-assets.html'), 'utf8')
    const standalone = await readFile(path.join(output, 'standalone.html'), 'utf8')
    assert.match(first, /href="\.\/02-assets\.html#chapter">Next chapter/)
    assert.match(second, /href="\.\/01-understand\.html#chapter">← Previous chapter/)
    assert.match(second, /href="\.\/01-understand\.html#chapter"/)
    assert.match(second, /href="\.\/02-assets\.html#chapter"/)
    assert.ok(standalone.indexOf('Understand the change') < standalone.indexOf('Inspect the assets'))
    assert.match(standalone, /id="chapter-01-understand"/)
    assert.match(standalone, /id="chapter-02-assets"/)
    assert.match(standalone, /id="chapter-01-understand-change-the-behavior"/)
    assert.match(standalone, /id="chapter-02-assets-update-the-asset"/)
    assert.doesNotMatch(standalone, /href="\.\/0[12]-[^"#]+\.html#chapter"/)
    const chapterIds = [...standalone.matchAll(/id="(chapter-\d{2}-[^"]+)"/g)].map((match) => match[1])
    assert.equal(new Set(chapterIds).size, chapterIds.length)
    const chapterLinks = [...standalone.matchAll(/href="#(chapter-\d{2}-[^"]+)"/g)].map((match) => match[1])
    assert.ok(chapterLinks.length > 0)
    assert.ok(chapterLinks.every((target) => chapterIds.includes(target)))
  })
})

test('unit-level findings use their owned section and immutable file target', async () => {
  const findings = [{
    id: 'binary-risk',
    status: 'verified',
    severity: 'P2',
    title: 'Check the binary asset',
    summary: 'The binary asset needs review.',
    trigger: 'The application loads the changed asset.',
    impact: 'The application can show the wrong image.',
    fix: 'Inspect the new asset before merge.',
    anchors: [{fileId: metadataFileId, unitId: metadataId}],
  }]
  const mdx = `# Understand the change

## Change the behavior

<Diff ref="${hunkId}@0:2" />

## Update the asset

<Diff ref="${metadataId}" />

The file itself is the evidence.

<Finding id="binary-risk" />
`
  await withBundle({mdx, findings}, async ({bundle, output}) => {
    await buildReviewBook({bundle, output})
    const html = await readFile(path.join(output, 'index.html'), 'utf8')
    assert.match(html, new RegExp(`class="finding-link" href="https://github\\.com/example/project/blob/${'3'.repeat(40)}/public/diagram\\.png"`))
  })

  const supportingCoverage = [
    {unitId: hunkId, section: 'Change the behavior', disposition: 'displayed'},
    {unitId: metadataId, section: 'Update the asset', disposition: 'supporting', reason: 'The binary asset supports this change.'},
  ]
  const supportingMdx = mdx.replace(`<Diff ref="${metadataId}" />\n\n`, '')
  await withBundle({mdx: supportingMdx, coverage: supportingCoverage, findings}, async ({bundle, output}) => {
    await buildReviewBook({bundle, output})
    const html = await readFile(path.join(output, 'index.html'), 'utf8')
    assert.match(html, /finding-binary-risk/)
    assert.doesNotMatch(html, new RegExp(`id="evidence-${metadataId.slice(5)}"`))
    assert.match(html, new RegExp(`class="finding-link" href="https://github\\.com/example/project/blob/${'3'.repeat(40)}/public/diagram\\.png"`))
  })

  await withBundle({mdx, findings, url: 'https://review.example.test/changes/42'}, async ({bundle, output}) => {
    await buildReviewBook({bundle, output})
    const html = await readFile(path.join(output, 'index.html'), 'utf8')
    assert.match(html, new RegExp(`class="finding-link" href="#evidence-${metadataId.slice(5)}"`))
  })

  const wrongSection = mdx.replace('## Update the asset', '## Change the asset').replace(
    '<Finding id="binary-risk" />',
    '## Unrelated risk\n\n<Finding id="binary-risk" />',
  )
  const changedCoverage = [
    {unitId: hunkId, section: 'Change the behavior', disposition: 'displayed'},
    {unitId: metadataId, section: 'Change the asset', disposition: 'displayed'},
  ]
  await withBundle({mdx: wrongSection, coverage: changedCoverage, findings}, async ({bundle, output}) => {
    await assert.rejects(buildReviewBook({bundle, output}), /must follow a Diff in section Unrelated risk/)
  })
})

test('rejects a unit-level anchor for a hunk', async () => {
  const findings = [{
    id: 'unsafe-value',
    status: 'verified',
    severity: 'P2',
    title: 'Validate the new value',
    summary: 'The new value has no validation.',
    trigger: 'The caller supplies an invalid value.',
    impact: 'An invalid value can enter the system.',
    fix: 'Validate the value before you store it.',
    anchors: [{fileId, unitId: hunkId}],
  }]
  await withBundle({findings}, async ({bundle, output}) => {
    await assert.rejects(buildReviewBook({bundle, output}), /hunk anchor must include side and line/)
  })
})

test('finding IDs must start with a lowercase letter', async () => {
  const findings = [{
    id: '1-invalid',
    status: 'verified',
    severity: 'P2',
    title: 'Validate the new value',
    summary: 'The new value has no validation.',
    trigger: 'The caller supplies an invalid value.',
    impact: 'An invalid value can enter the system.',
    fix: 'Validate the value before you store it.',
    anchors: [{fileId, unitId: hunkId, side: 'new', line: 1}],
  }]
  await withBundle({findings}, async ({bundle, output}) => {
    await assert.rejects(buildReviewBook({bundle, output}), /invalid finding ID/)
  })
})

test('deleted evidence links to the frozen merge-base blob', () => {
  const mergeBase = '2'.repeat(40)
  const head = '3'.repeat(40)
  const target = pullRequestDiffTarget(
    'https://github.com/example/project/pull/42',
    mergeBase,
    head,
    {
      name: 'deleted-line',
      file: {
        id: fileId,
        path: 'src/new-name.ts',
        oldPath: 'src/old name.ts',
        status: 'renamed',
        isBinary: false,
        units: [hunk],
      },
      unit: hunk,
      lines: [hunk.lines[0]!],
    },
  )
  assert.deepEqual(target, {
    href: `https://github.com/example/project/blob/${mergeBase}/src/old%20name.ts#L1`,
    label: 'Open src/old name.ts at line 1 of the frozen merge base',
  })
})

test('renders supported Unicode bidirectional controls as visible evidence text', async () => {
  await withBundle({}, async ({bundle, output}) => {
    const runPath = path.join(bundle, 'run.json')
    const findingsPath = path.join(bundle, 'findings.json')
    const run = JSON.parse(await readFile(runPath, 'utf8'))
    const findings = JSON.parse(await readFile(findingsPath, 'utf8'))
    run.subject.url = 'https://review.example.test/changes/42'
    run.subject.repository = 'example/\u061c\u202aproject'
    run.files[0].path = 'src/\u200e\u202bvalue.ts'
    run.files[0].units[0].lines[1].text = 'const value = "\u202d"'
    run.files[1].units[0].label = 'Binary \u200f\u202c change'
    findings.findings[0].title = 'Validate the \u202e new value'
    findings.findings[0].summary = 'The \u2066 new value has no validation.'
    findings.findings[0].trigger = 'The caller supplies an \u2067 invalid value.'
    findings.findings[0].impact = 'An invalid value can \u2068 enter the system.'
    findings.findings[0].fix = 'Validate the value \u2069 before you store it.'
    await writeFile(runPath, JSON.stringify(run))
    await writeFile(findingsPath, JSON.stringify(findings))

    await buildReviewBook({bundle, output})
    const html = await readFile(path.join(output, 'index.html'), 'utf8')
    assert.doesNotMatch(html, /[\u061c\u200e\u200f\u202a-\u202e\u2066-\u2069]/)
    const visibleText = html.replace(/<[^>]*>/g, '')
    for (const code of ['061C', '200E', '200F', '202A', '202B', '202C', '202D', '202E', '2066', '2067', '2068', '2069']) {
      assert.match(visibleText, new RegExp(`⟦U\\+${code}⟧`))
    }
  })
})

test('rejects Unicode bidirectional controls in authored MDX', async () => {
  await withBundle({mdx: '# Unsafe chapter\n\nThis text contains \u202e a hidden control.'}, async ({bundle, output}) => {
    await assert.rejects(buildReviewBook({bundle, output}), /authored MDX cannot contain Unicode bidirectional controls/)
  })
})

test('allows safe links and validates a frozen pull request URL', () => {
  assert.equal(safeLink('javascript:alert(1)'), false)
  assert.equal(safeLink('data:text/html,bad'), false)
  assert.equal(safeLink('./local.html'), false)
  assert.equal(safeLink('../parent.html'), false)
  assert.equal(safeLink('https://'), false)
  assert.equal(safeLink('https:///missing-host'), false)
  assert.equal(safeLink('https://user:secret@example.com/docs'), false)
  assert.equal(safeLink('https://example.com/docs'), true)
  assert.equal(safeLink('#evidence'), true)
  assert.equal(pullRequestUrl('https://github.com/example/project/pull/42', 'example/project'), 'https://github.com/example/project/pull/42')
  assert.equal(
    pullRequestUrl('https://github.enterprise.test/example/project/pull/42', 'example/project'),
    'https://github.enterprise.test/example/project/pull/42',
  )
  assert.equal(pullRequestUrl('', 'example/project'), null)
  assert.throws(
    () => pullRequestUrl('https://example.com/other/project/pull/42', 'example/project'),
    /repository does not match/,
  )
  assert.throws(
    () => pullRequestUrl('https://github.com/example/project/pull/42?x=1', 'example/project'),
    /cannot contain credentials, a port, a query, or a fragment/,
  )
  assert.throws(
    () => pullRequestUrl('https://github.com/example/project/pull/42#x', 'example/project'),
    /cannot contain credentials, a port, a query, or a fragment/,
  )
  assert.throws(
    () => pullRequestUrl('https://github.enterprise.test:8443/example/project/pull/42', 'example/project'),
    /cannot contain credentials, a port, a query, or a fragment/,
  )
  assert.equal(pullRequestUrl('https://github.com/example/project/issues/42', 'example/project'), null)
  assert.throws(() => pullRequestUrl('http://github.com/example/project/pull/42', 'example/project'), /HTTPS URL/)
})

test('selects only in-bounds evidence that contains a changed line', () => {
  assert.deepEqual(selectEvidence(hunk, {lineOffset: 0, lineCount: 2}, 'test'), hunk.lines)
  assert.throws(() => selectEvidence(hunk, {lineOffset: 1, lineCount: 2}, 'test'), /outside/)
  assert.throws(() => selectEvidence(hunk, {lineOffset: 0, lineCount: 25}, 'test'), /more than 24 lines/)
})
