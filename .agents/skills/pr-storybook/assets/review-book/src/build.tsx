import {compile, run as runMdx} from '@mdx-js/mdx'
import React, {createElement, isValidElement, type ComponentType, type ReactNode} from 'react'
import {renderToStaticMarkup} from 'react-dom/server'
import * as jsxRuntime from 'react/jsx-runtime'
import remarkGfm from 'remark-gfm'
import {createHighlighter} from 'shiki'
import {createHash} from 'node:crypto'
import {mkdir, mkdtemp, readFile, readdir, rename, rm, writeFile} from 'node:fs/promises'
import {fileURLToPath, pathToFileURL} from 'node:url'
import path from 'node:path'

type ReviewLine = {
  kind: 'context' | 'addition' | 'deletion' | 'note'
  oldLine: number | null
  newLine: number | null
  text: string
}

type HunkUnit = {
  id: string
  kind: 'hunk'
  header: string
  oldRange: {start: number; count: number}
  newRange: {start: number; count: number}
  lines: ReviewLine[]
}

type MetadataUnit = {
  id: string
  kind: 'metadata'
  label: string
}

type ReviewUnit = HunkUnit | MetadataUnit

type ReviewFile = {
  id: string
  path: string
  oldPath: string | null
  status: string
  isBinary: boolean
  units: ReviewUnit[]
}

type Run = {
  schemaVersion: number
  runId: string
  subject: {
    repository: string
    title: string
    url: string
    base: string
    mergeBase: string
    head: string
  }
  files: ReviewFile[]
}

type UnitFindingAnchor = {
  fileId: string
  unitId: string
}

type LineFindingAnchor = UnitFindingAnchor & {
  side: 'old' | 'new'
  line: number
}

type FindingAnchor = UnitFindingAnchor | LineFindingAnchor

type Finding = {
  id: string
  status: string
  severity: string
  title: string
  summary: string
  trigger: string
  impact: string
  fix: string
  anchors: FindingAnchor[]
}

type Findings = {
  runId: string
  findings: Finding[]
}

type BookConfig = {
  schemaVersion: 1
  runId: string
  title: string
}

type CoverageDisposition = 'displayed' | 'supporting' | 'mechanical'

type CoverageEntry = {
  unitId: string
  section: string
  disposition: CoverageDisposition
  reason?: string
}

type ChapterSidecar = {
  schemaVersion: 1
  runId: string
  chapter: string
  coverage: CoverageEntry[]
}

type UnitRecord = {file: ReviewFile; unit: ReviewUnit}

type ResolvedEvidence = UnitRecord & {
  name: string
  lines: ReviewLine[] | null
}

type FindingTarget =
  | {kind: 'line'; evidence: ResolvedEvidence; anchor: LineFindingAnchor}
  | {kind: 'unit'; evidence: ResolvedEvidence; displayed: boolean}

type Chapter = {
  slug: string
  sourcePath: string
  outputName: string
  sidecar: ChapterSidecar
  coverageByUnit: Map<string, CoverageEntry>
  title: string
  sections: Set<string>
  resolvedEvidence: Map<string, ResolvedEvidence>
  displayedUnitIds: Set<string>
  findingIds: string[]
  findingTargets: Map<string, FindingTarget>
}

type TreeAttribute = {type: string; name?: string; value?: unknown}

type TreeNode = {
  type: string
  depth?: number
  value?: string
  lang?: string | null
  meta?: string | null
  url?: string
  name?: string | null
  attributes?: TreeAttribute[]
  children?: TreeNode[]
}

type BuildArguments = {bundle: string; output: string}
type CliArguments = {bundle: string; output: string | null; validateOnly: boolean}
type ValidatedBook = {
  config: BookConfig
  run: Run
  pullUrl: string | null
  findingById: Map<string, Finding>
  chapters: Chapter[]
}

const RUNTIME_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const SAFE_ID = /^[a-z][a-z0-9-]*$/
const HASH_ID = /^(?:sha256:)[a-f0-9]{64}$/
const FILE_ID = /^file:[a-f0-9]{64}$/
const UNIT_ID = /^unit:[a-f0-9]{64}$/
const HUNK_REF = /^(unit:[a-f0-9]{64})@([0-9]+):([1-9][0-9]*)$/
const METADATA_REF = /^(unit:[a-f0-9]{64})$/
const CHAPTER_FILE = /^(\d{2})-[a-z0-9]+(?:-[a-z0-9]+)*\.mdx$/
const BIDI_CONTROL = /[\u061c\u200e\u200f\u202a-\u202e\u2066-\u2069]/g
const BIDI_CONTROL_PRESENT = /[\u061c\u200e\u200f\u202a-\u202e\u2066-\u2069]/

const ALLOWED_NODES = new Set([
  'root',
  'paragraph',
  'text',
  'heading',
  'strong',
  'emphasis',
  'delete',
  'inlineCode',
  'code',
  'blockquote',
  'list',
  'listItem',
  'thematicBreak',
  'break',
  'link',
  'linkReference',
  'definition',
  'table',
  'tableRow',
  'tableCell',
])

function fail(location: string, message: string): never {
  throw new Error(`${location}: ${message}`)
}

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function exactKeys(value: Record<string, unknown>, keys: string[], location: string): void {
  const actual = Object.keys(value).sort()
  const expected = [...keys].sort()
  if (actual.length !== expected.length || actual.some((key, index) => key !== expected[index])) {
    fail(location, `needs exactly these keys: ${expected.join(', ')}`)
  }
}

function nonemptyString(value: unknown, location: string): string {
  if (typeof value !== 'string' || !value.trim()) fail(location, 'must be a non-empty string')
  return value
}

function readBook(value: unknown): BookConfig {
  if (!isObject(value)) fail('book.json', 'must contain an object')
  exactKeys(value, ['schemaVersion', 'runId', 'title'], 'book.json')
  if (value.schemaVersion !== 1) fail('book.json.schemaVersion', 'must be 1')
  const runId = nonemptyString(value.runId, 'book.json.runId')
  if (!HASH_ID.test(runId)) fail('book.json.runId', 'must be a lowercase SHA-256 ID')
  const title = nonemptyString(value.title, 'book.json.title')
  if (BIDI_CONTROL_PRESENT.test(title)) fail('book.json.title', 'cannot contain Unicode bidirectional controls')
  return {schemaVersion: 1, runId, title}
}

function readCoverageEntry(value: unknown, location: string): CoverageEntry {
  if (!isObject(value)) fail(location, 'must be an object')
  const disposition = value.disposition
  if (disposition !== 'displayed' && disposition !== 'supporting' && disposition !== 'mechanical') {
    fail(`${location}.disposition`, 'must be displayed, supporting, or mechanical')
  }
  const expectedKeys = disposition === 'displayed'
    ? ['unitId', 'section', 'disposition']
    : ['unitId', 'section', 'disposition', 'reason']
  exactKeys(value, expectedKeys, location)
  const unitId = nonemptyString(value.unitId, `${location}.unitId`)
  if (!UNIT_ID.test(unitId)) fail(`${location}.unitId`, 'must be a lowercase review unit ID')
  const section = nonemptyString(value.section, `${location}.section`)
  if (disposition === 'displayed') return {unitId, section, disposition}
  const reason = nonemptyString(value.reason, `${location}.reason`).trim()
  if (reason.length > 240) fail(`${location}.reason`, 'must contain at most 240 characters')
  return {unitId, section, disposition, reason}
}

function readSidecar(value: unknown, location: string, expectedRunId: string): ChapterSidecar {
  if (!isObject(value)) fail(location, 'must contain an object')
  exactKeys(value, ['schemaVersion', 'runId', 'chapter', 'coverage'], location)
  if (value.schemaVersion !== 1) fail(`${location}.schemaVersion`, 'must be 1')
  const runId = nonemptyString(value.runId, `${location}.runId`)
  if (!HASH_ID.test(runId)) fail(`${location}.runId`, 'must be a lowercase SHA-256 ID')
  if (runId !== expectedRunId) fail(`${location}.runId`, 'does not match book.json')
  const chapter = nonemptyString(value.chapter, `${location}.chapter`)
  if (!Array.isArray(value.coverage)) fail(`${location}.coverage`, 'must be an array')
  return {
    schemaVersion: 1,
    runId,
    chapter,
    coverage: value.coverage.map((entry, index) => readCoverageEntry(entry, `${location}.coverage[${index}]`)),
  }
}

async function readJson(filePath: string): Promise<unknown> {
  try {
    return JSON.parse(await readFile(filePath, 'utf8')) as unknown
  } catch (error) {
    fail(filePath, error instanceof Error ? error.message : 'cannot read JSON')
  }
}

function textFromNode(node: TreeNode): string {
  if (typeof node.value === 'string') return node.value
  return (node.children ?? []).map(textFromNode).join('')
}

function visibleBidiControls(value: string): string {
  return value.replace(BIDI_CONTROL, (character) => {
    const codePoint = character.codePointAt(0)!.toString(16).toUpperCase().padStart(4, '0')
    return `⟦U+${codePoint}⟧`
  })
}

function literalAttribute(node: TreeNode, expectedName: string, location: string): string {
  const attributes = node.attributes ?? []
  if (attributes.length !== 1) fail(location, `${node.name} needs one literal ${expectedName} attribute`)
  const attribute = attributes[0]
  if (attribute?.type !== 'mdxJsxAttribute' || attribute.name !== expectedName || typeof attribute.value !== 'string') {
    fail(location, `${node.name} needs one literal ${expectedName} attribute`)
  }
  return attribute.value
}

function safeLink(url: string): boolean {
  if (url.startsWith('#')) return true
  if (!/^https:\/\/[^/]/.test(url)) return false
  try {
    const parsed = new URL(url)
    return parsed.protocol === 'https:' && Boolean(parsed.hostname) && !parsed.username && !parsed.password
  } catch {
    return false
  }
}

function pullRequestUrl(value: string, repository: string): string | null {
  if (!value) return null
  let parsed: URL
  try {
    parsed = new URL(value)
  } catch {
    fail('run.json.subject.url', 'is invalid')
  }
  if (parsed.protocol !== 'https:' || !parsed.hostname) fail('run.json.subject.url', 'must be an HTTPS URL')
  const match = /^\/([^/]+\/[^/]+)\/pull\/([1-9][0-9]*)\/?$/.exec(parsed.pathname)
  if (!match) return null
  if (parsed.username || parsed.password || parsed.port || parsed.search || parsed.hash) {
    fail('run.json.subject.url', 'a pull request URL cannot contain credentials, a port, a query, or a fragment')
  }
  if (match[1] !== repository) fail('run.json.subject.url', 'repository does not match run.json.subject.repository')
  return `${parsed.origin}/${repository}/pull/${match[2]}`
}

function selectEvidence(
  unit: HunkUnit,
  reference: {lineOffset: number; lineCount: number},
  location: string,
): ReviewLine[] {
  if (!Number.isInteger(reference.lineOffset) || reference.lineOffset < 0) {
    fail(location, 'the line offset must be a non-negative integer')
  }
  if (!Number.isInteger(reference.lineCount) || reference.lineCount < 1) {
    fail(location, 'the line count must be a positive integer')
  }
  if (reference.lineCount > 24) fail(location, 'a Diff excerpt cannot contain more than 24 lines')
  const end = reference.lineOffset + reference.lineCount
  if (end > unit.lines.length) fail(location, `the selection is outside ${unit.id}`)
  const lines = unit.lines.slice(reference.lineOffset, end)
  if (!lines.some((line) => line.kind === 'addition' || line.kind === 'deletion')) {
    fail(location, `the selection in ${unit.id} has no changed line`)
  }
  return lines
}

function isLineAnchor(anchor: FindingAnchor): anchor is LineFindingAnchor {
  return 'side' in anchor && 'line' in anchor
}

function evidenceContainsAnchor(evidence: ResolvedEvidence, anchor: FindingAnchor): boolean {
  if (!isLineAnchor(anchor)) return false
  if (evidence.lines === null || evidence.file.id !== anchor.fileId || evidence.unit.id !== anchor.unitId) return false
  return evidence.lines.some((line) => (
    anchor.side === 'new'
      ? line.kind === 'addition' && line.newLine === anchor.line
      : line.kind === 'deletion' && line.oldLine === anchor.line
  ))
}

function validateAllowedNode(node: TreeNode, location: string, isRootChild = false): void {
  if (node.type === 'mdxjsEsm' || node.type === 'mdxFlowExpression' || node.type === 'mdxTextExpression' || node.type === 'html') {
    fail(location, `${node.type} is not allowed`)
  }
  if (node.type === 'mdxJsxTextElement') fail(location, 'inline JSX is not allowed')
  if (node.type === 'mdxJsxFlowElement') {
    if (!isRootChild) fail(location, 'Diff and Finding must be direct chapter blocks')
    if (node.name !== 'Diff' && node.name !== 'Finding') fail(location, `component ${String(node.name)} is not allowed`)
    if ((node.children ?? []).length !== 0) fail(location, `${node.name} cannot contain children`)
    literalAttribute(node, node.name === 'Diff' ? 'ref' : 'id', location)
    return
  }
  if (!ALLOWED_NODES.has(node.type)) fail(location, `node type ${node.type} is not allowed`)
  if ((node.type === 'link' || node.type === 'definition') && (typeof node.url !== 'string' || !safeLink(node.url))) {
    fail(location, 'link target is not allowed')
  }
  if (node.type === 'code' && (node.meta?.trim() ?? '')) fail(location, 'code metadata is not allowed')
  for (const [index, child] of (node.children ?? []).entries()) {
    validateAllowedNode(child, `${location}.${index}`, false)
  }
}

function chapterGuard(options: {
  chapter: Chapter
  unitById: Map<string, UnitRecord>
  findingById: Map<string, Finding>
}) {
  return () => (tree: TreeNode) => {
    const usedEvidence = new Set<string>()
    const titles: string[] = []
    let activeSection: string | null = null

    for (const [index, node] of (tree.children ?? []).entries()) {
      const location = `${options.chapter.sourcePath}.${index}`
      validateAllowedNode(node, location, true)

      if (node.type === 'heading') {
        if (node.depth !== 1 && node.depth !== 2 && node.depth !== 3) {
          fail(location, 'heading depth must be H1, H2, or H3')
        }
        const title = textFromNode(node).trim()
        if (!title) fail(location, 'heading text cannot be empty')
        if (options.chapter.sections.has(title)) fail(location, `heading ${title} is repeated`)
        options.chapter.sections.add(title)
        activeSection = title
        if (node.depth === 1) titles.push(title)
        continue
      }

      if (node.type !== 'mdxJsxFlowElement') continue
      if (!activeSection) fail(location, `${node.name} must follow a heading`)

      if (node.name === 'Diff') {
        const diffRef = literalAttribute(node, 'ref', location)
        if (usedEvidence.has(diffRef)) fail(location, `evidence ${diffRef} is repeated`)
        const hunkMatch = HUNK_REF.exec(diffRef)
        const metadataMatch = METADATA_REF.exec(diffRef)
        const unitId = hunkMatch?.[1] ?? metadataMatch?.[1]
        if (!unitId) fail(location, 'Diff ref is invalid')
        const record = options.unitById.get(unitId)
        if (!record) fail(location, `evidence ${diffRef} uses an unknown review unit`)
        const coverage = options.chapter.coverageByUnit.get(unitId)
        if (!coverage) fail(location, `evidence ${diffRef} is outside this chapter coverage`)
        if (coverage.disposition !== 'displayed') fail(location, `evidence ${diffRef} is not marked as displayed`)
        if (coverage.section !== activeSection) {
          fail(location, `evidence ${diffRef} is under ${activeSection}, not its assigned section ${coverage.section}`)
        }

        let lines: ReviewLine[] | null
        let name: string
        if (record.unit.kind === 'hunk') {
          if (!hunkMatch) fail(location, 'a hunk Diff ref needs @offset:count')
          const lineOffset = Number(hunkMatch[2])
          const lineCount = Number(hunkMatch[3])
          lines = selectEvidence(record.unit, {lineOffset, lineCount}, location)
          name = `${unitId.slice(5)}-${lineOffset}-${lineCount}`
        } else {
          if (hunkMatch) fail(location, 'a metadata Diff ref cannot have a line range')
          lines = null
          name = unitId.slice(5)
        }
        options.chapter.resolvedEvidence.set(diffRef, {name, ...record, lines})
        options.chapter.displayedUnitIds.add(unitId)
        usedEvidence.add(diffRef)
        continue
      }

      const findingId = literalAttribute(node, 'id', location)
      if (!SAFE_ID.test(findingId)) fail(location, 'Finding id is invalid')
      const finding = options.findingById.get(findingId)
      if (!finding || finding.status !== 'verified') fail(location, `finding ${findingId} is unknown or is not verified`)
      options.chapter.findingIds.push(findingId)
    }

    if (titles.length !== 1 || !titles[0]) fail(options.chapter.sourcePath, 'chapter needs exactly one level-one heading')
    options.chapter.title = titles[0]

    let placementSection: string | null = null
    let precedingDiffs: string[] = []
    for (const [index, node] of (tree.children ?? []).entries()) {
      const location = `${options.chapter.sourcePath}.${index}`
      if (node.type === 'heading') {
        placementSection = textFromNode(node).trim()
        precedingDiffs = []
        continue
      }
      if (node.type !== 'mdxJsxFlowElement') continue
      if (node.name === 'Diff') {
        precedingDiffs.push(literalAttribute(node, 'ref', location))
        continue
      }
      const findingId = literalAttribute(node, 'id', location)
      const finding = options.findingById.get(findingId)
      const lineEvidence = [...precedingDiffs].reverse().map((reference) => (
        options.chapter.resolvedEvidence.get(reference)
      )).find((evidence) => (
        evidence && finding?.anchors.some((anchor) => evidenceContainsAnchor(evidence, anchor))
      ))
      if (finding && lineEvidence) {
        const anchor = finding.anchors.find((candidate): candidate is LineFindingAnchor => (
          evidenceContainsAnchor(lineEvidence, candidate)
        ))
        if (!anchor) fail(location, `finding ${findingId} has no matching line anchor`)
        options.chapter.findingTargets.set(findingId, {kind: 'line', evidence: lineEvidence, anchor})
        continue
      }

      const unitTarget = finding?.anchors.map((anchor) => {
        if (isLineAnchor(anchor)) return null
        const record = options.unitById.get(anchor.unitId)
        const coverage = options.chapter.coverageByUnit.get(anchor.unitId)
        if (!record || record.file.id !== anchor.fileId || coverage?.section !== placementSection) return null
        const displayedEvidence = [...options.chapter.resolvedEvidence.values()].find((evidence) => evidence.unit.id === anchor.unitId)
        return {
          kind: 'unit' as const,
          evidence: displayedEvidence ?? {name: anchor.unitId.slice(5), ...record, lines: null},
          displayed: Boolean(displayedEvidence),
        }
      }).find((target): target is Extract<FindingTarget, {kind: 'unit'}> => target !== null)
      if (unitTarget) {
        options.chapter.findingTargets.set(findingId, unitTarget)
        continue
      }

      const anchoredEarlierDiff = [...precedingDiffs].reverse().find((reference) => {
        const evidence = options.chapter.resolvedEvidence.get(reference)
        return evidence && finding?.anchors.some((anchor) => evidenceContainsAnchor(evidence, anchor))
      })
      if (!finding || !anchoredEarlierDiff) {
        fail(location, `finding ${findingId} must follow a Diff in section ${String(placementSection)} that contains its changed-line anchor`)
      }
    }
  }
}

function validateCoverage(
  chapters: Chapter[],
  unitById: Map<string, UnitRecord>,
  findingById: Map<string, Finding>,
): void {
  const owner = new Map<string, string>()
  const shownFindings = new Set<string>()

  for (const chapter of chapters) {
    if (chapter.sidecar.chapter !== chapter.slug) fail(chapter.sourcePath, 'sidecar chapter does not match the filename')
    for (const entry of chapter.sidecar.coverage) {
      if (!unitById.has(entry.unitId)) fail(chapter.sourcePath, `coverage contains unknown unit ${entry.unitId}`)
      const previous = owner.get(entry.unitId)
      if (previous) fail(chapter.sourcePath, `review unit ${entry.unitId} is also assigned to ${previous}`)
      owner.set(entry.unitId, chapter.slug)
      if (!chapter.sections.has(entry.section)) fail(chapter.sourcePath, `coverage section ${entry.section} is not a chapter heading`)
      if (entry.disposition === 'displayed' && !chapter.displayedUnitIds.has(entry.unitId)) {
        fail(chapter.sourcePath, `displayed unit ${entry.unitId} has no Diff in its assigned section`)
      }
    }
    for (const findingId of chapter.findingIds) {
      if (shownFindings.has(findingId)) fail(chapter.sourcePath, `finding ${findingId} is repeated`)
      shownFindings.add(findingId)
    }
  }

  for (const unitId of unitById.keys()) {
    if (!owner.has(unitId)) fail('book', `review unit ${unitId} is not assigned to a chapter`)
  }
  for (const finding of findingById.values()) {
    if (finding.status === 'verified' && !shownFindings.has(finding.id)) {
      fail('book', `verified finding ${finding.id} is not shown in a chapter`)
    }
  }
}

function slugify(value: string): string {
  return value.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '') || 'section'
}

function reactText(value: ReactNode): string {
  if (typeof value === 'string' || typeof value === 'number') return String(value)
  if (Array.isArray(value)) return value.map(reactText).join('')
  if (isValidElement<{children?: ReactNode}>(value)) return reactText(value.props.children)
  return ''
}

function lineAnchorId(name: string, side: 'old' | 'new', line: number): string {
  return `evidence-${name}-${side}-${line}`
}

function lineAnchor(line: ReviewLine, name: string): string | undefined {
  if (line.kind === 'addition' && line.newLine !== null) return lineAnchorId(name, 'new', line.newLine)
  if (line.kind === 'deletion' && line.oldLine !== null) return lineAnchorId(name, 'old', line.oldLine)
  return undefined
}

function pullRequestDiffTarget(
  pullUrl: string | null,
  mergeBase: string,
  head: string,
  evidence: ResolvedEvidence,
): {href: string; label: string} | null {
  if (!pullUrl) return null
  const parsedPullUrl = new URL(pullUrl)
  const repositoryRoot = `${parsedPullUrl.origin}${parsedPullUrl.pathname.replace(/\/pull\/[1-9][0-9]*$/, '')}`
  const encodedPath = evidence.file.path.split('/').map(encodeURIComponent).join('/')
  if (evidence.lines === null) {
    if (evidence.file.status !== 'deleted') {
      return {
        href: `${repositoryRoot}/blob/${head}/${encodedPath}`,
        label: visibleBidiControls(`Open ${evidence.file.path} at the frozen head`),
      }
    }
    const oldPath = evidence.file.oldPath ?? evidence.file.path
    const encodedOldPath = oldPath.split('/').map(encodeURIComponent).join('/')
    return {
      href: `${repositoryRoot}/blob/${mergeBase}/${encodedOldPath}`,
      label: visibleBidiControls(`Open the deleted file ${oldPath} at the frozen merge base`),
    }
  }
  const changedLine = evidence.lines.find((line) => line.kind === 'addition')
    ?? evidence.lines.find((line) => line.kind === 'deletion')
  if (!changedLine) fail(evidence.unit.id, 'displayed evidence has no changed line')
  const line = changedLine.kind === 'addition' ? changedLine.newLine : changedLine.oldLine
  if (line === null) fail(evidence.unit.id, 'changed line has no source line number')
  if (changedLine.kind === 'addition' && evidence.file.status !== 'deleted') {
    return {
      href: `${repositoryRoot}/blob/${head}/${encodedPath}#L${line}`,
      label: visibleBidiControls(`Open ${evidence.file.path} at line ${line} of the frozen head`),
    }
  }
  const oldPath = evidence.file.oldPath ?? evidence.file.path
  const encodedOldPath = oldPath.split('/').map(encodeURIComponent).join('/')
  return {
    href: `${repositoryRoot}/blob/${mergeBase}/${encodedOldPath}#L${line}`,
    label: visibleBidiControls(`Open ${oldPath} at line ${line} of the frozen merge base`),
  }
}

function pullRequestLineTarget(
  pullUrl: string | null,
  mergeBase: string,
  head: string,
  evidence: ResolvedEvidence,
  anchor: LineFindingAnchor,
): {href: string; label: string} | null {
  if (!pullUrl) return null
  const parsedPullUrl = new URL(pullUrl)
  const repositoryRoot = `${parsedPullUrl.origin}${parsedPullUrl.pathname.replace(/\/pull\/[1-9][0-9]*$/, '')}`
  const filePath = anchor.side === 'new' ? evidence.file.path : evidence.file.oldPath ?? evidence.file.path
  const revision = anchor.side === 'new' ? head : mergeBase
  const encodedPath = filePath.split('/').map(encodeURIComponent).join('/')
  const revisionLabel = anchor.side === 'new' ? 'head' : 'merge base'
  return {
    href: `${repositoryRoot}/blob/${revision}/${encodedPath}#L${anchor.line}`,
    label: visibleBidiControls(`Open ${filePath} at line ${anchor.line} of the frozen ${revisionLabel}`),
  }
}

function sourceLanguage(filePath: string): string {
  const fileName = path.basename(filePath).toLowerCase()
  if (fileName === 'dockerfile') return 'dockerfile'
  const extension = path.extname(fileName)
  const languageByExtension: Record<string, string> = {
    '.bash': 'bash', '.c': 'c', '.cc': 'cpp', '.cpp': 'cpp', '.cs': 'csharp', '.css': 'css',
    '.go': 'go', '.graphql': 'graphql', '.h': 'c', '.hpp': 'cpp', '.html': 'html', '.java': 'java',
    '.js': 'javascript', '.json': 'json', '.jsx': 'javascript', '.kt': 'kotlin', '.kts': 'kotlin',
    '.md': 'markdown', '.mdx': 'markdown', '.php': 'php', '.py': 'python', '.rb': 'ruby', '.rs': 'rust',
    '.sh': 'bash', '.sql': 'sql', '.swift': 'swift', '.tf': 'hcl', '.toml': 'toml', '.ts': 'typescript',
    '.tsx': 'typescript', '.xml': 'xml', '.yaml': 'yaml', '.yml': 'yaml',
  }
  return languageByExtension[extension] ?? 'text'
}

function accessibleLineLabel(line: ReviewLine): string {
  const text = visibleBidiControls(line.text) || 'blank line'
  if (line.kind === 'addition') return `Added line ${line.newLine}: ${text}`
  if (line.kind === 'deletion') return `Removed line ${line.oldLine}: ${text}`
  if (line.kind === 'note') return `Diff note: ${text}`
  return `Unchanged line ${line.newLine ?? line.oldLine}: ${text}`
}

function chapterAnchor(chapter: Chapter): string {
  return `chapter-${chapter.slug}`
}

function navigation(chapters: Chapter[], active: Chapter | null, singlePage = false): ReactNode {
  return (
    <nav className="chapter-nav" aria-label="Chapters">
      <p className="chapter-nav-label">Chapters</p>
      <ol>
        {chapters.map((chapter, index) => (
          <li key={chapter.slug}>
            <a
              href={singlePage ? `#${chapterAnchor(chapter)}` : `./${chapter.outputName}#chapter`}
              aria-current={chapter === active ? 'page' : undefined}
            >
              <span className="chapter-number">{String(index + 1).padStart(2, '0')}</span>
              <span>{chapter.title}</span>
            </a>
          </li>
        ))}
      </ol>
    </nav>
  )
}

function createComponents(options: {
  chapter: Chapter
  findingById: Map<string, Finding>
  highlighter: Awaited<ReturnType<typeof createHighlighter>>
  pullRequestUrl: string | null
  mergeBase: string
  head: string
  chapterHeadingId?: string
  headingIdPrefix?: string
  preferLocalFindingLinks?: boolean
}) {
  const usedSlugs = new Map<string, number>()
  const headingId = (children: ReactNode) => {
    const base = slugify(reactText(children))
    const count = (usedSlugs.get(base) ?? 0) + 1
    usedSlugs.set(base, count)
    const id = count === 1 ? base : `${base}-${count}`
    return options.headingIdPrefix ? `${options.headingIdPrefix}-${id}` : id
  }

  const evidenceForFinding = (finding: Finding): {href: string; label: string} | null => {
    const target = options.chapter.findingTargets.get(finding.id)
    if (!target) return null
    if (target.kind === 'line') {
      const platformTarget = pullRequestLineTarget(
        options.pullRequestUrl,
        options.mergeBase,
        options.head,
        target.evidence,
        target.anchor,
      )
      if (platformTarget && !options.preferLocalFindingLinks) return platformTarget
      return {
          href: `#${lineAnchorId(target.evidence.name, target.anchor.side, target.anchor.line)}`,
          label: visibleBidiControls(`${path.basename(target.evidence.file.path)} · ${target.anchor.side === 'new' ? 'after' : 'before'} line ${target.anchor.line}`),
      }
    }
    const platformTarget = pullRequestDiffTarget(
      options.pullRequestUrl,
      options.mergeBase,
      options.head,
      target.evidence,
    )
    if (platformTarget && !options.preferLocalFindingLinks) return platformTarget
    if (target.displayed) {
      return {
        href: `#evidence-${target.evidence.name}`,
        label: visibleBidiControls(path.basename(target.evidence.file.path)),
      }
    }
    return null
  }

  const PathLabel = ({evidence}: {evidence: ResolvedEvidence}) => {
    const target = pullRequestDiffTarget(options.pullRequestUrl, options.mergeBase, options.head, evidence)
    const displayPath = visibleBidiControls(evidence.file.path)
    if (!target) return <span className="code-path">{displayPath}</span>
    return <a className="code-path" href={target.href} target="_blank" rel="noreferrer" aria-label={target.label}>{displayPath}</a>
  }

  const EvidenceBlock = ({evidence}: {evidence: ResolvedEvidence}) => {
    if (evidence.unit.kind === 'metadata' || evidence.lines === null) {
      const label = visibleBidiControls(evidence.unit.kind === 'metadata' ? evidence.unit.label : 'Metadata-only change')
      const displayPath = visibleBidiControls(evidence.file.path)
      return (
        <section className="metadata-change" id={`evidence-${evidence.name}`} aria-label={`${label}: ${displayPath}`}>
          <PathLabel evidence={evidence} />
          <p>{label}</p>
        </section>
      )
    }
    const language = sourceLanguage(evidence.file.path)
    const displayLines = evidence.lines.map((line) => ({...line, text: visibleBidiControls(line.text)}))
    const tokenLines = displayLines.map((line) => (
      options.highlighter.codeToTokens(line.text || ' ', {lang: language as never, theme: 'github-dark-default'}).tokens[0] ?? []
    ))
    return (
      <figure className="evidence-block" id={`evidence-${evidence.name}`}>
        <figcaption className="code-header"><PathLabel evidence={evidence} /></figcaption>
        <div className="code-scroll">
          <pre><code className="code-lines" role="list" aria-label={`Changes in ${visibleBidiControls(path.basename(evidence.file.path))}`}>
            {displayLines.map((line, index) => (
              <span className={`source-line ${line.kind}`} id={lineAnchor(line, evidence.name)} role="listitem" aria-label={accessibleLineLabel(line)} key={`${index}-${line.oldLine}-${line.newLine}`}>
                <span className="line-number" aria-hidden="true">{line.oldLine ?? ''}</span>
                <span className="line-number" aria-hidden="true">{line.newLine ?? ''}</span>
                <span className="line-marker" aria-hidden="true">{line.kind === 'addition' ? '+' : line.kind === 'deletion' ? '−' : line.kind === 'note' ? '!' : ' '}</span>
                <span className="line-text" aria-hidden="true">
                  {tokenLines[index]?.map((token, tokenIndex) => <span style={{color: token.color}} key={tokenIndex}>{token.content}</span>)}
                </span>
              </span>
            ))}
          </code></pre>
        </div>
      </figure>
    )
  }

  const PlainCode = ({language, code}: {language: string; code: string}) => {
    const loaded = options.highlighter.getLoadedLanguages()
    const languageName = loaded.includes(language as never) ? language : 'text'
    const result = options.highlighter.codeToTokens(code, {lang: languageName as never, theme: 'github-dark-default'})
    return (
      <figure className="code-block">
        <div className="code-scroll">
          <pre><code className="code-lines">
            {result.tokens.map((tokens, index) => (
              <span className="plain-code-line" key={index}>
                {tokens.map((token, tokenIndex) => <span style={{color: token.color}} key={tokenIndex}>{token.content}</span>)}
                {'\n'}
              </span>
            ))}
          </code></pre>
        </div>
      </figure>
    )
  }

  const Pre = ({children}: {children?: ReactNode}) => {
    if (!isValidElement<{children?: ReactNode; className?: string}>(children)) {
      fail(options.chapter.sourcePath, 'code fence did not compile to one code element')
    }
    const code = reactText(children.props.children).replace(/\n$/, '')
    const language = children.props.className?.replace(/^language-/, '') ?? 'text'
    return <PlainCode language={language} code={code} />
  }

  const DiffBlock = ({ref: diffRef}: {ref: string}) => {
    const resolved = options.chapter.resolvedEvidence.get(diffRef)
    if (!resolved) fail(options.chapter.sourcePath, `compiled evidence ${diffRef} is unknown`)
    return <EvidenceBlock evidence={resolved} />
  }

  const FindingBlock = ({id}: {id: string}) => {
    const finding = options.findingById.get(id)
    if (!finding || finding.status !== 'verified') fail(options.chapter.sourcePath, `cannot render finding ${id}`)
    const evidence = evidenceForFinding(finding)
    return (
      <aside className="finding" id={`finding-${id}`} aria-label={visibleBidiControls(`${finding.severity} finding: ${finding.title}`)}>
        <p className="finding-label">{visibleBidiControls(finding.severity)} finding</p>
        <p className="finding-title"><strong>{visibleBidiControls(finding.title)}</strong></p>
        <p>{visibleBidiControls(finding.summary)}</p>
        <p><strong>Trigger:</strong> {visibleBidiControls(finding.trigger)}</p>
        <p>{visibleBidiControls(finding.impact)}</p>
        <p><strong>Suggested fix:</strong> {visibleBidiControls(finding.fix)}</p>
        {evidence ? <a className="finding-link" href={evidence.href}>See {evidence.label}</a> : null}
      </aside>
    )
  }

  return {
    h1: ({children}: {children?: ReactNode}) => <h1 id={options.chapterHeadingId ?? 'chapter'} tabIndex={-1}>{children}</h1>,
    h2: ({children}: {children?: ReactNode}) => <h2 id={headingId(children)}>{children}</h2>,
    h3: ({children}: {children?: ReactNode}) => <h3 id={headingId(children)}>{children}</h3>,
    code: ({children}: {children?: ReactNode}) => <code>{children}</code>,
    pre: Pre,
    Diff: DiffBlock,
    Finding: FindingBlock,
  }
}

function Page({config, run, chapters, chapter, content, cssVersion}: {
  config: BookConfig
  run: Run
  chapters: Chapter[]
  chapter: Chapter
  content: ReactNode
  cssVersion: string
}) {
  const index = chapters.indexOf(chapter)
  const previous = chapters[index - 1]
  const next = chapters[index + 1]
  return (
    <html lang="en">
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <meta name="color-scheme" content="dark" />
        <meta httpEquiv="Content-Security-Policy" content="default-src 'none'; style-src 'self' 'unsafe-inline'; img-src data:; font-src 'self'; base-uri 'none'; form-action 'none'" />
        <title>{`${chapter.title} — ${config.title}`}</title>
        <link rel="stylesheet" href={`./assets/book.css?v=${cssVersion}`} />
      </head>
      <body>
        <a className="skip-link" href="#chapter">Skip to chapter</a>
        <header className="book-header">
          <p className="book-kicker">PR Storybook</p>
          <p className="book-title">{config.title}</p>
          <p className="book-snapshot">{visibleBidiControls(run.subject.repository)} · {run.subject.mergeBase.slice(0, 10)} → {run.subject.head.slice(0, 10)}</p>
        </header>
        <details className="mobile-chapters">
          <summary>Chapters</summary>
          {navigation(chapters, chapter)}
        </details>
        <div className="book-shell">
          <aside className="book-sidebar">{navigation(chapters, chapter)}</aside>
          <main className="book-main">
            <article className="story">{content}</article>
            <nav className="chapter-footer" aria-label="Chapter pages">
              {previous ? <a href={`./${previous.outputName}#chapter`}>← Previous chapter</a> : <span className="footer-spacer" />}
              {next ? <a href={`./${next.outputName}#chapter`}>Next chapter →</a> : <span className="footer-spacer" />}
            </nav>
          </main>
        </div>
      </body>
    </html>
  )
}

function StandalonePage({config, run, chapters, chapterContents, css}: {
  config: BookConfig
  run: Run
  chapters: Chapter[]
  chapterContents: Array<{chapter: Chapter; content: ReactNode}>
  css: string
}) {
  const firstChapterId = chapterAnchor(chapters[0]!)
  return (
    <html lang="en">
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <meta name="color-scheme" content="dark" />
        <meta httpEquiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; img-src data:; base-uri 'none'; form-action 'none'" />
        <title>{config.title}</title>
        <style>{css}</style>
      </head>
      <body>
        <a className="skip-link" href={`#${firstChapterId}`}>Skip to first chapter</a>
        <header className="book-header">
          <p className="book-kicker">PR Storybook</p>
          <p className="book-title">{config.title}</p>
          <p className="book-snapshot">{visibleBidiControls(run.subject.repository)} · {run.subject.mergeBase.slice(0, 10)} → {run.subject.head.slice(0, 10)}</p>
        </header>
        <details className="mobile-chapters">
          <summary>Chapters</summary>
          {navigation(chapters, null, true)}
        </details>
        <div className="book-shell">
          <aside className="book-sidebar">{navigation(chapters, null, true)}</aside>
          <main className="book-main">
            {chapterContents.map(({chapter, content}, index) => {
              const previous = chapters[index - 1]
              const next = chapters[index + 1]
              return (
                <section className="standalone-chapter" aria-labelledby={chapterAnchor(chapter)} key={chapter.slug}>
                  <article className="story">{content}</article>
                  <nav className="chapter-footer" aria-label={`${visibleBidiControls(chapter.title)} chapter pages`}>
                    {previous ? <a href={`#${chapterAnchor(previous)}`}>← Previous chapter</a> : <span className="footer-spacer" />}
                    {next ? <a href={`#${chapterAnchor(next)}`}>Next chapter →</a> : <span className="footer-spacer" />}
                  </nav>
                </section>
              )
            })}
          </main>
        </div>
      </body>
    </html>
  )
}

function validateRun(value: unknown, expectedRunId: string): Run {
  if (!isObject(value)) fail('run.json', 'must contain an object')
  if (value.schemaVersion !== 1) fail('run.json.schemaVersion', 'must be 1')
  if (value.runId !== expectedRunId) fail('run.json.runId', 'does not match book.json')
  if (!isObject(value.subject)) fail('run.json.subject', 'must be an object')
  for (const key of ['repository', 'title', 'base', 'mergeBase', 'head']) nonemptyString(value.subject[key], `run.json.subject.${key}`)
  if (typeof value.subject.url !== 'string') fail('run.json.subject.url', 'must be a string')
  if (!Array.isArray(value.files) || value.files.length === 0) fail('run.json.files', 'must be a non-empty array')
  return value as unknown as Run
}

function validateFindings(value: unknown, expectedRunId: string): Findings {
  if (!isObject(value)) fail('findings.json', 'must contain an object')
  if (value.runId !== expectedRunId) fail('findings.json.runId', 'does not match book.json')
  if (!Array.isArray(value.findings)) fail('findings.json.findings', 'must be an array')
  return value as unknown as Findings
}

function buildIndexes(run: Run, findings: Findings): {
  unitById: Map<string, UnitRecord>
  findingById: Map<string, Finding>
} {
  const unitById = new Map<string, UnitRecord>()
  for (const [fileIndex, file] of run.files.entries()) {
    if (!isObject(file) || typeof file.id !== 'string' || typeof file.path !== 'string' || !Array.isArray(file.units)) {
      fail(`run.json.files[${fileIndex}]`, 'has an invalid file record')
    }
    for (const [unitIndex, unit] of file.units.entries()) {
      const location = `run.json.files[${fileIndex}].units[${unitIndex}]`
      if (!isObject(unit) || typeof unit.id !== 'string' || !UNIT_ID.test(unit.id)) fail(location, 'has an invalid review unit ID')
      if (unit.kind !== 'hunk' && unit.kind !== 'metadata') fail(location, 'must be a hunk or metadata unit')
      if (unitById.has(unit.id)) fail(location, `review unit ${unit.id} is repeated`)
      if (unit.kind === 'hunk' && !Array.isArray(unit.lines)) fail(location, 'hunk lines must be an array')
      if (unit.kind === 'metadata' && typeof unit.label !== 'string') fail(location, 'metadata label must be a string')
      unitById.set(unit.id, {file, unit: unit as ReviewUnit})
    }
  }

  const findingById = new Map<string, Finding>()
  for (const [index, finding] of findings.findings.entries()) {
    const location = `findings.json.findings[${index}]`
    if (!isObject(finding) || typeof finding.id !== 'string' || !SAFE_ID.test(finding.id)) fail(location, 'has an invalid finding ID')
    if (findingById.has(finding.id)) fail(location, `finding ${finding.id} is repeated`)
    for (const key of ['status', 'severity', 'title', 'summary', 'trigger', 'impact', 'fix'] as const) {
      nonemptyString(finding[key], `${location}.${key}`)
    }
    if (!Array.isArray(finding.anchors)) fail(location, 'anchors must be an array')
    for (const [anchorIndex, anchor] of finding.anchors.entries()) {
      const anchorLocation = `${location}.anchors[${anchorIndex}]`
      if (!isObject(anchor)) fail(anchorLocation, 'must be an object')
      const isLineLevel = 'side' in anchor || 'line' in anchor
      exactKeys(anchor, isLineLevel ? ['fileId', 'unitId', 'side', 'line'] : ['fileId', 'unitId'], anchorLocation)
      if (typeof anchor.fileId !== 'string' || !FILE_ID.test(anchor.fileId)) fail(`${anchorLocation}.fileId`, 'must be a lowercase file ID')
      if (typeof anchor.unitId !== 'string' || !UNIT_ID.test(anchor.unitId)) fail(`${anchorLocation}.unitId`, 'must be a lowercase review unit ID')
      if (isLineLevel) {
        if (anchor.side !== 'old' && anchor.side !== 'new') fail(`${anchorLocation}.side`, 'must be old or new')
        if (!Number.isInteger(anchor.line) || Number(anchor.line) < 1) fail(`${anchorLocation}.line`, 'must be a positive integer')
      } else if (unitById.get(anchor.unitId)?.unit.kind === 'hunk') {
        fail(anchorLocation, 'a hunk anchor must include side and line')
      }
    }
    findingById.set(finding.id, finding as unknown as Finding)
  }
  return {unitById, findingById}
}

async function readChapters(
  bundle: string,
  expectedRunId: string,
  unitById: Map<string, UnitRecord>,
  findingById: Map<string, Finding>,
): Promise<Chapter[]> {
  const chaptersRoot = path.join(bundle, 'chapters')
  const names = await readdir(chaptersRoot)
  const chapterFiles = names.filter((name) => name.endsWith('.mdx')).sort()
  if (chapterFiles.length === 0) fail(chaptersRoot, 'no chapter files found')
  const sidecarFiles = new Set(names.filter((name) => name.endsWith('.evidence.json')))
  const chapters: Chapter[] = []

  for (const [index, fileName] of chapterFiles.entries()) {
    const match = CHAPTER_FILE.exec(fileName)
    if (!match) fail(path.join(chaptersRoot, fileName), 'chapter filename must use NN-slug.mdx')
    const expectedNumber = String(index + 1).padStart(2, '0')
    if (match[1] !== expectedNumber) fail(path.join(chaptersRoot, fileName), `chapter number must be ${expectedNumber}`)
    const slug = fileName.slice(0, -4)
    const sidecarName = `${slug}.evidence.json`
    if (!sidecarFiles.delete(sidecarName)) fail(path.join(chaptersRoot, fileName), `needs matching ${sidecarName}`)
    const sourcePath = path.join(chaptersRoot, fileName)
    const sidecar = readSidecar(await readJson(path.join(chaptersRoot, sidecarName)), sidecarName, expectedRunId)
    const coverageByUnit = new Map<string, CoverageEntry>()
    for (const entry of sidecar.coverage) {
      if (coverageByUnit.has(entry.unitId)) fail(sidecarName, `review unit ${entry.unitId} is repeated`)
      coverageByUnit.set(entry.unitId, entry)
    }
    const chapter: Chapter = {
      slug,
      sourcePath,
      outputName: `${slug}.html`,
      sidecar,
      coverageByUnit,
      title: '',
      sections: new Set(),
      resolvedEvidence: new Map(),
      displayedUnitIds: new Set(),
      findingIds: [],
      findingTargets: new Map(),
    }
    const source = await readFile(sourcePath, 'utf8')
    if (BIDI_CONTROL_PRESENT.test(source)) fail(sourcePath, 'authored MDX cannot contain Unicode bidirectional controls')
    const compiled = await compile({path: sourcePath, value: source}, {
      outputFormat: 'function-body',
      jsxImportSource: 'react',
      remarkPlugins: [remarkGfm, chapterGuard({chapter, unitById, findingById})],
    })
    Object.assign(chapter, {compiled: String(compiled)})
    chapters.push(chapter)
  }
  if (sidecarFiles.size > 0) fail(chaptersRoot, `orphan sidecar ${[...sidecarFiles].sort()[0]}`)
  return chapters
}

function outputPathSafety(bundle: string, output: string): void {
  if (output !== path.join(bundle, 'site')) {
    fail('command line', '--output must equal the bundle site directory')
  }
}

async function publishSite(stage: string, output: string): Promise<void> {
  const parent = path.dirname(output)
  const backup = await mkdtemp(path.join(parent, '.pr-storybook-old-'))
  await rm(backup, {recursive: true})
  let movedOldSite = false
  try {
    try {
      await rename(output, backup)
      movedOldSite = true
    } catch (error) {
      if ((error as NodeJS.ErrnoException).code !== 'ENOENT') throw error
    }
    try {
      await rename(stage, output)
    } catch (error) {
      if (movedOldSite) {
        try {
          await rename(backup, output)
          movedOldSite = false
        } catch (restoreError) {
          throw new AggregateError([error, restoreError], `site publish failed; the old site remains at ${backup}`)
        }
      }
      throw error
    }
    if (movedOldSite) {
      await rm(backup, {recursive: true})
      movedOldSite = false
    }
  } finally {
    if (!movedOldSite) await rm(backup, {recursive: true, force: true})
  }
}

function parseArguments(argv: string[]): CliArguments {
  const values = new Map<string, string>()
  let validateOnly = false
  for (let index = 0; index < argv.length;) {
    const name = argv[index]
    if (name === '--validate-only') {
      if (validateOnly) fail('command line', '--validate-only is repeated')
      validateOnly = true
      index += 1
      continue
    }
    const value = argv[index + 1]
    if ((name !== '--bundle' && name !== '--output') || !value || value.startsWith('--')) {
      fail('command line', 'usage: node build.mjs --bundle BUNDLE (--output BUNDLE/site | --validate-only)')
    }
    if (values.has(name)) fail('command line', `${name} is repeated`)
    values.set(name, value)
    index += 2
  }
  const bundle = values.get('--bundle')
  const output = values.get('--output')
  if (!bundle || validateOnly === Boolean(output)) {
    fail('command line', 'usage: node build.mjs --bundle BUNDLE (--output BUNDLE/site | --validate-only)')
  }
  return {bundle: path.resolve(bundle), output: output ? path.resolve(output) : null, validateOnly}
}

async function loadReviewBook(bundleValue: string): Promise<ValidatedBook> {
  const bundle = path.resolve(bundleValue)
  const config = readBook(await readJson(path.join(bundle, 'book.json')))
  const run = validateRun(await readJson(path.join(bundle, 'run.json')), config.runId)
  const findings = validateFindings(await readJson(path.join(bundle, 'findings.json')), config.runId)
  const pullUrl = pullRequestUrl(run.subject.url, run.subject.repository)
  const {unitById, findingById} = buildIndexes(run, findings)
  const chapters = await readChapters(bundle, config.runId, unitById, findingById)
  validateCoverage(chapters, unitById, findingById)
  return {config, run, pullUrl, findingById, chapters}
}

export async function validateReviewBook({bundle}: {bundle: string}): Promise<void> {
  await loadReviewBook(bundle)
}

export async function buildReviewBook(argumentsValue: BuildArguments): Promise<void> {
  const bundle = path.resolve(argumentsValue.bundle)
  const output = path.resolve(argumentsValue.output)
  outputPathSafety(bundle, output)
  const {config, run, pullUrl, findingById, chapters} = await loadReviewBook(bundle)

  const highlighter = await createHighlighter({
    themes: ['github-dark-default'],
    langs: [
      'text', 'bash', 'c', 'cpp', 'csharp', 'css', 'dockerfile', 'go', 'graphql', 'hcl', 'html',
      'java', 'javascript', 'json', 'kotlin', 'markdown', 'php', 'python', 'ruby', 'rust', 'sql',
      'swift', 'toml', 'typescript', 'xml', 'yaml',
    ],
  })
  await mkdir(path.dirname(output), {recursive: true})
  const stage = await mkdtemp(path.join(path.dirname(output), '.pr-storybook-stage-'))
  try {
    const css = await readFile(path.join(RUNTIME_ROOT, 'src', 'styles.css'), 'utf8')
    const cssVersion = createHash('sha256').update(css).digest('hex').slice(0, 12)
    await mkdir(path.join(stage, 'assets'), {recursive: true})
    await writeFile(path.join(stage, 'assets', 'book.css'), css, 'utf8')
    const standaloneContents: Array<{chapter: Chapter; content: ReactNode}> = []

    for (const [index, chapter] of chapters.entries()) {
      const compiled = (chapter as Chapter & {compiled: string}).compiled
      const module = await runMdx(compiled, {...jsxRuntime, baseUrl: pathToFileURL(chapter.sourcePath)}) as {default: ComponentType<{components: Record<string, ComponentType<never>>}>}
      const components = createComponents({
        chapter,
        findingById,
        highlighter,
        pullRequestUrl: pullUrl,
        mergeBase: run.subject.mergeBase,
        head: run.subject.head,
      })
      const content = createElement(module.default, {components: components as never})
      const html = '<!doctype html>' + renderToStaticMarkup(
        <Page config={config} run={run} chapters={chapters} chapter={chapter} content={content} cssVersion={cssVersion} />,
      )
      await writeFile(path.join(stage, chapter.outputName), html, 'utf8')
      if (index === 0) await writeFile(path.join(stage, 'index.html'), html, 'utf8')

      const standaloneModule = await runMdx(compiled, {...jsxRuntime, baseUrl: pathToFileURL(chapter.sourcePath)}) as {default: ComponentType<{components: Record<string, ComponentType<never>>}>}
      const standaloneId = chapterAnchor(chapter)
      const standaloneComponents = createComponents({
        chapter,
        findingById,
        highlighter,
        pullRequestUrl: pullUrl,
        mergeBase: run.subject.mergeBase,
        head: run.subject.head,
        chapterHeadingId: standaloneId,
        headingIdPrefix: standaloneId,
        preferLocalFindingLinks: true,
      })
      standaloneContents.push({
        chapter,
        content: createElement(standaloneModule.default, {components: standaloneComponents as never}),
      })
    }

    const standaloneHtml = '<!doctype html>' + renderToStaticMarkup(
      <StandalonePage config={config} run={run} chapters={chapters} chapterContents={standaloneContents} css={css} />,
    )
    await writeFile(path.join(stage, 'standalone.html'), standaloneHtml, 'utf8')

    await publishSite(stage, output)
  } finally {
    highlighter.dispose()
    await rm(stage, {recursive: true, force: true})
  }
}

export async function main(argv = process.argv.slice(2)): Promise<void> {
  const argumentsValue = parseArguments(argv)
  if (argumentsValue.validateOnly) {
    await validateReviewBook({bundle: argumentsValue.bundle})
    console.log(`Validated PR Storybook bundle at ${argumentsValue.bundle}`)
    return
  }
  if (!argumentsValue.output) fail('command line', '--output is required for a build')
  await buildReviewBook({bundle: argumentsValue.bundle, output: argumentsValue.output})
  console.log(`Built PR Storybook in ${argumentsValue.output}`)
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  await main()
}

export {chapterGuard, parseArguments, pullRequestDiffTarget, pullRequestUrl, readBook, readSidecar, safeLink, selectEvidence, validateCoverage}
