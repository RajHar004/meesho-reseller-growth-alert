import React, { useState } from 'react';
import { 
  Database, 
  ShieldCheck, 
  FileText, 
  Bot, 
  Folder, 
  FileCode, 
  Terminal, 
  CheckCircle2, 
  AlertTriangle, 
  Layers, 
  ChevronRight,
  GitBranch,
  KeyRound,
  ExternalLink,
  Code2
} from 'lucide-react';

interface FileNode {
  path: string;
  name: string;
  type: 'file' | 'folder';
  stage: string;
  purpose: string;
  description: string;
  children?: FileNode[];
}

const fileTreeData: FileNode[] = [
  {
    path: 'README.md',
    name: 'README.md',
    type: 'file',
    stage: 'Root Documentation',
    purpose: 'System documentation, run commands, workflow mapping, and academic integrity references.',
    description: 'Documents how to regenerate the seeded dataset, run each part in order, confirms 0 API keys required, and maps stages to enterprise reporting workflows.'
  },
  {
    path: 'data',
    name: 'data/',
    type: 'folder',
    stage: 'Seeded Data Layer',
    purpose: 'Deterministic seeded dataset and relational SQLite database.',
    description: 'Holds reproducible CSV and SQLite assets generated with a fixed PRNG seed (42).',
    children: [
      {
        path: 'data/generate_dataset.py',
        name: 'generate_dataset.py',
        type: 'file',
        stage: 'Data Generation',
        purpose: 'Deterministic synthetic dataset generator using random.Random(42).',
        description: 'Creates 24 resellers across 4 regions and 900 orders across Apr/May/Jun 2026. Explicitly guarantees zero-order reseller RS024.'
      },
      {
        path: 'data/resellers.csv',
        name: 'resellers.csv',
        type: 'file',
        stage: 'Raw Data',
        purpose: 'Seeded master table of 24 resellers with ID, name, city, region, and join_date.',
        description: 'Includes RS001 to RS024 across North, South, East, and West regions.'
      },
      {
        path: 'data/orders.csv',
        name: 'orders.csv',
        type: 'file',
        stage: 'Raw Data',
        purpose: '900 orders partitioned across 3 months (300 orders each for April, May, June 2026).',
        description: 'Contains category distributions, quantities, unit prices, order dates, and statuses.'
      },
      {
        path: 'data/meesho_reseller.db',
        name: 'meesho_reseller.db',
        type: 'file',
        stage: 'Relational Database',
        purpose: 'SQLite database populated with normalized resellers and orders tables.',
        description: 'Direct SQL execution target for Part 1 analytical business queries.'
      }
    ]
  },
  {
    path: 'part1_sql',
    name: 'part1_sql/',
    type: 'folder',
    stage: 'Part 1: SQL Business Query Engine',
    purpose: 'Standardized SQL queries answering standing category operations questions.',
    description: 'Computes monthly revenue aggregations, region rollups, top resellers, inactivity audits, and AOV.',
    children: [
      {
        path: 'part1_sql/queries.sql',
        name: 'queries.sql',
        type: 'file',
        stage: 'SQL Queries',
        purpose: 'SQL statements answering 5 analytical business questions against meesho_reseller.db.',
        description: 'Calculates monthly category revenue, region revenue, top spenders (>50k), zero-order LEFT JOIN check, and June Delivered AOV.'
      },
      {
        path: 'part1_sql/output',
        name: 'output/',
        type: 'folder',
        stage: 'SQL Query Artifacts',
        purpose: 'Pre-computed CSV exports from SQL query executions.',
        description: 'Standard output folder consumed downstream by Part 2 and Part 4.',
        children: [
          {
            path: 'part1_sql/output/monthly_category_revenue.csv',
            name: 'monthly_category_revenue.csv',
            type: 'file',
            stage: 'Data Feed',
            purpose: '15-row ground-truth monthly category revenue feed.',
            description: 'Feeds directly into Part 2 engine validation and Part 4 agent runs (month, category, revenue, n_orders).'
          }
        ]
      }
    ]
  },
  {
    path: 'part2_engine',
    name: 'part2_engine/',
    type: 'folder',
    stage: 'Part 2: Python Guardrail & Growth-Detection Engine',
    purpose: 'Mathematical calculations and feed validation rules tested via unit test suites.',
    description: 'Converts vague business rules into testable mathematical invariants and boundary conditions.',
    children: [
      {
        path: 'part2_engine/growth_engine.py',
        name: 'growth_engine.py',
        type: 'file',
        stage: 'Core Engine',
        purpose: 'Three core functions: mom_growth(), is_flagged(), and validate_feed().',
        description: 'Implements tri-state boundary logic (flagged/not_flagged/escalate_exact_boundary) and row-level feed schema validation.'
      },
      {
        path: 'part2_engine/test_growth_engine.py',
        name: 'test_growth_engine.py',
        type: 'file',
        stage: 'Test Suite',
        purpose: 'Given-When-Then unit tests asserting mathematical and guardrail behavior.',
        description: 'Tests 4 canonical scenarios including May Ethnic Wear (+77.1%), June Beauty (+5.67%), exact 8.0% boundary, and corrupted feed detection.'
      },
      {
        path: 'part2_engine/fixtures',
        name: 'fixtures/',
        type: 'folder',
        stage: 'Test Fixtures',
        purpose: 'Standardized feeds for deterministic test verification.',
        description: 'Negative and positive test CSV feeds.',
        children: [
          {
            path: 'part2_engine/fixtures/corrupted_feed.csv',
            name: 'corrupted_feed.csv',
            type: 'file',
            stage: 'Negative Fixture',
            purpose: 'Corrupted feed with 3 deliberate anomalies (negative revenue, missing category, missing revenue).',
            description: 'Verifies validate_feed halts on lines 3, 4, and 6 with exact line-numbered error messages.'
          },
          {
            path: 'part2_engine/fixtures/monthly_category_revenue.csv',
            name: 'monthly_category_revenue.csv',
            type: 'file',
            stage: 'Positive Fixture',
            purpose: 'Validated copy of 15-row ground truth feed.',
            description: 'Confirms that valid data yields (True, []) with zero validation errors.'
          }
        ]
      }
    ]
  },
  {
    path: 'part3_narrative',
    name: 'part3_narrative/',
    type: 'folder',
    stage: 'Part 3: Reliable AI Narrative & Prompt-Pack Report',
    purpose: 'Zero-hallucination narrative generation, 4-tier refinement, and PII masking.',
    description: 'Ensures executive updates strictly trace to computed numbers and protect partner confidentiality.',
    children: [
      {
        path: 'part3_narrative/prompt_pack.md',
        name: 'prompt_pack.md',
        type: 'file',
        stage: 'Prompt Spec',
        purpose: 'Reusable prompt specification in 4 structured sections.',
        description: 'Documents Trigger, Input list, Prompt template (Context -> Insight -> Implication), and 4-point verification checklist.'
      },
      {
        path: 'part3_narrative/narrative_report.md',
        name: 'narrative_report.md',
        type: 'file',
        stage: 'Executive Narrative',
        purpose: 'Worked narrative blocks, self-evaluations, and chart-choice justifications.',
        description: 'Provides May and June Ethnic Wear narratives, checklist self-scores, and text-only chart justifications.'
      },
      {
        path: 'part3_narrative/masking.py',
        name: 'masking.py',
        type: 'file',
        stage: 'PII Masking',
        purpose: 'Privacy enforcement functions: alias_for() and assert_no_raw_names_leak().',
        description: 'Converts RS019 -> ALIAS-19 and verifies raw reseller names never leak into executive summaries.'
      }
    ]
  },
  {
    path: 'part4_agent',
    name: 'part4_agent/',
    type: 'folder',
    stage: 'Part 4: Agentic Workflow Spec + Mock Agent Runner',
    purpose: 'End-to-end guarded orchestration, subtask planner, and human approval gateway.',
    description: 'Ties Parts 1-3 into a unified pipeline emitting structured JSON audit payloads.',
    children: [
      {
        path: 'part4_agent/agent_spec.md',
        name: 'agent_spec.md',
        type: 'file',
        stage: 'Architecture Spec',
        purpose: 'Comprehensive specification of the 5 agent components and guardrails.',
        description: 'Details Goal, Tools, Memory, Planner, Feedback loop, stopping conditions, and agent-level test specs.'
      },
      {
        path: 'part4_agent/mock_agent_runner.py',
        name: 'mock_agent_runner.py',
        type: 'file',
        stage: 'Orchestrator',
        purpose: 'Executable orchestration module exposing run(month, prev_csv, curr_csv).',
        description: 'Imports Part 2 math, executes 8 subtasks, applies 3-alert flood cap, and emits standardized JSON with approval flags.'
      }
    ]
  }
];

export default function App() {
  const [selectedFile, setSelectedFile] = useState<FileNode>(fileTreeData[0]);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      {/* Top Header */}
      <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur px-6 py-4 sticky top-0 z-20">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-pink-500/10 border border-pink-500/30 flex items-center justify-center text-pink-400">
              <Layers className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-lg font-bold text-slate-100 tracking-tight">
                  Meesho Reseller Growth &amp; Alert Intelligence Pipeline
                </h1>
                <span className="px-2 py-0.5 text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded">
                  Scaffold Ready
                </span>
              </div>
              <p className="text-xs text-slate-400">
                Code-First Architecture: SQL → Python Guardrails → AI Narrative → Agent → Human Approval
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2 text-xs">
            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-slate-800/80 border border-slate-700 text-slate-300">
              <KeyRound className="w-3.5 h-3.5 text-amber-400" />
              <span>Zero API Keys Required</span>
            </div>
            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-slate-800/80 border border-slate-700 text-slate-300">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
              <span>Deterministic Flow</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="max-w-7xl mx-auto w-full p-6 flex-1 flex flex-col gap-6">
        
        {/* Pipeline Architecture Bar */}
        <section className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 shadow-sm">
          <h2 className="text-xs uppercase font-bold tracking-wider text-slate-400 mb-3 flex items-center gap-2">
            <GitBranch className="w-4 h-4 text-pink-400" />
            Integrated Pipeline Architecture &amp; Data Contract
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
            <div className="p-3.5 rounded-lg bg-slate-950/60 border border-slate-800 hover:border-slate-700 transition">
              <div className="flex items-center gap-2 text-xs font-bold text-indigo-400 mb-1">
                <Database className="w-4 h-4" /> Part 1: SQL Engine
              </div>
              <p className="text-xs text-slate-400 leading-relaxed">
                Computes real numbers from SQLite database. Feeds verified monthly category revenue directly into Part 2.
              </p>
              <div className="mt-2 text-[10px] text-slate-500 font-mono">meesho_reseller.db → monthly_category_revenue.csv</div>
            </div>

            <div className="p-3.5 rounded-lg bg-slate-950/60 border border-slate-800 hover:border-slate-700 transition">
              <div className="flex items-center gap-2 text-xs font-bold text-amber-400 mb-1">
                <ShieldCheck className="w-4 h-4" /> Part 2: Guardrails
              </div>
              <p className="text-xs text-slate-400 leading-relaxed">
                Feed validation guardrail &amp; Month-on-Month math. Classifies into flagged, not_flagged, or boundary escalation.
              </p>
              <div className="mt-2 text-[10px] text-slate-500 font-mono">validate_feed() | mom_growth() | is_flagged()</div>
            </div>

            <div className="p-3.5 rounded-lg bg-slate-950/60 border border-slate-800 hover:border-slate-700 transition">
              <div className="flex items-center gap-2 text-xs font-bold text-cyan-400 mb-1">
                <FileText className="w-4 h-4" /> Part 3: Narrative &amp; PII
              </div>
              <p className="text-xs text-slate-400 leading-relaxed">
                Context → Insight → Implication prompt-pack template, 4-tier review checklist, and ALIAS-XX reseller masking.
              </p>
              <div className="mt-2 text-[10px] text-slate-500 font-mono">alias_for() | prompt_pack.md | masking.py</div>
            </div>

            <div className="p-3.5 rounded-lg bg-slate-950/60 border border-slate-800 hover:border-slate-700 transition">
              <div className="flex items-center gap-2 text-xs font-bold text-pink-400 mb-1">
                <Bot className="w-4 h-4" /> Part 4: Agent &amp; Approval
              </div>
              <p className="text-xs text-slate-400 leading-relaxed">
                8-step subtask planner. Prevents notification flooding (caps top 3 alerts). All messages held for human approval.
              </p>
              <div className="mt-2 text-[10px] text-slate-500 font-mono">mock_agent_runner.py → structured JSON</div>
            </div>
          </div>
        </section>

        {/* Repository File Tree & Inspector */}
        <section className="grid grid-cols-1 lg:grid-cols-12 gap-6 flex-1 items-start">
          
          {/* File Tree Panel */}
          <div className="lg:col-span-5 bg-slate-900/60 border border-slate-800 rounded-xl p-4 flex flex-col">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-3">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2">
                <Folder className="w-4 h-4 text-pink-400" />
                Repository Structure
              </span>
              <span className="text-[11px] text-slate-500 font-mono">16 target files</span>
            </div>

            <div className="space-y-1 font-mono text-xs overflow-y-auto max-h-[520px] pr-1">
              {fileTreeData.map((node) => (
                <FileTreeNode
                  key={node.path}
                  node={node}
                  selectedPath={selectedFile.path}
                  onSelect={(item) => setSelectedFile(item)}
                />
              ))}
            </div>
          </div>

          {/* Details / File Inspector Panel */}
          <div className="lg:col-span-7 bg-slate-900/60 border border-slate-800 rounded-xl p-5 flex flex-col gap-4">
            <div className="flex items-start justify-between border-b border-slate-800 pb-4">
              <div>
                <div className="flex items-center gap-2">
                  <span className="px-2 py-0.5 text-[11px] font-semibold bg-pink-500/10 text-pink-300 border border-pink-500/30 rounded">
                    {selectedFile.stage}
                  </span>
                  <span className="text-xs text-slate-400 font-mono">{selectedFile.type}</span>
                </div>
                <h3 className="text-lg font-bold text-slate-100 font-mono mt-1.5">
                  {selectedFile.path}
                </h3>
              </div>
            </div>

            <div className="space-y-4">
              <div>
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-1">
                  Primary Purpose
                </h4>
                <p className="text-sm text-slate-200 leading-relaxed bg-slate-950/50 p-3 rounded-lg border border-slate-800/80">
                  {selectedFile.purpose}
                </p>
              </div>

              <div>
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-1">
                  Design Contract &amp; Contents
                </h4>
                <p className="text-xs text-slate-300 leading-relaxed bg-slate-950/50 p-3 rounded-lg border border-slate-800/80">
                  {selectedFile.description}
                </p>
              </div>

              <div className="border border-slate-800 rounded-lg p-3.5 bg-slate-950/40">
                <h4 className="text-xs font-bold text-slate-300 mb-2 flex items-center gap-2">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                  Key Constraints &amp; Acceptance Requirements
                </h4>
                <ul className="text-xs text-slate-400 space-y-1.5 list-disc list-inside">
                  <li>Zero API keys: pipeline executes deterministically offline without LLM tokens.</li>
                  <li>Pure code deliverable: no rendered images, screenshots, or PDFs.</li>
                  <li>Part 4 imports Part 2 math functions unmodified instead of reimplementing.</li>
                  <li>Strict schema validation with immediate Hard Stop on corrupt feeds.</li>
                </ul>
              </div>
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800 py-3 px-6 text-center text-xs text-slate-500">
        Meesho Reseller Growth &amp; Alert Intelligence Pipeline • Capstone Project Scaffold
      </footer>
    </div>
  );
}

function FileTreeNode({
  node,
  selectedPath,
  onSelect,
  level = 0
}: {
  node: FileNode;
  selectedPath: string;
  onSelect: (node: FileNode) => void;
  level?: number;
}) {
  const isSelected = selectedPath === node.path;
  const isFolder = node.type === 'folder';

  return (
    <div>
      <button
        onClick={() => onSelect(node)}
        className={`w-full text-left px-2 py-1.5 rounded flex items-center gap-2 transition ${
          isSelected
            ? 'bg-pink-500/20 text-pink-200 border border-pink-500/40'
            : 'text-slate-300 hover:bg-slate-800/60'
        }`}
        style={{ paddingLeft: `${Math.max(level * 16 + 8, 8)}px` }}
      >
        {isFolder ? (
          <Folder className="w-3.5 h-3.5 text-amber-400 shrink-0" />
        ) : (
          <FileCode className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
        )}
        <span className="truncate">{node.name}</span>
      </button>

      {node.children && (
        <div className="space-y-0.5">
          {node.children.map((child) => (
            <FileTreeNode
              key={child.path}
              node={child}
              selectedPath={selectedPath}
              onSelect={onSelect}
              level={level + 1}
            />
          ))}
        </div>
      )}
    </div>
  );
}
