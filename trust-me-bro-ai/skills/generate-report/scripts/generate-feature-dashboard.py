#!/usr/bin/env python3
"""generate-feature-dashboard.py — aggregates cross-service feature scenarios into an interactive dashboard.

Scans work/Scenario/ across microservice repositories for matching feature scenarios (e.g. BIZ_AI, BROADCAST, ALL),
extracts metadata, progress tracks, test data, and task graphs, and generates a self-contained,
fully interactive HTML feature dashboard.

Usage:
  python3 generate-feature-dashboard.py --feature BIZ_AI
  python3 generate-feature-dashboard.py --feature BROADCAST --output broadcast-dashboard.html
  python3 generate-feature-dashboard.py --services-dir /path/to/services --feature ALL
  python3 generate-feature-dashboard.py --check
"""

import argparse
import html as html_mod
import json
import os
import re
import sys
from pathlib import Path

esc = html_mod.escape
VOID_TAGS = {"meta", "br", "img", "link", "input", "hr"}

STAGE_LABELS = [
    "Get Requirement",
    "Create Test Data",
    "Create Task",
    "Execute Backlog",
    "Api Test",
    "Acceptance Review",
]

TYPE_TAGS = {
    "unit-test": "t-unit-test",
    "integration-test": "t-integration-test",
    "component-test": "t-component-test",
    "code-task": "t-code-task",
    "api-test": "t-api-test",
    "env-setup": "t-env-setup",
    "interface": "t-interface",
}

CSS = """*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg-primary:#f1f5f9;
  --bg-card:#ffffff;
  --bg-subtle:#f8fafc;
  --text-main:#0f172a;
  --text-muted:#475569;
  --text-subtle:#94a3b8;
  --primary:#6366f1;
  --primary-hover:#4f46e5;
  --primary-light:#e0e7ff;
  --primary-subtle:#eef2ff;
  --success:#16a34a;
  --success-light:#dcfce7;
  --success-text:#166534;
  --warning:#d97706;
  --warning-light:#fef9c3;
  --warning-text:#854d0e;
  --danger:#dc2626;
  --danger-light:#fee2e2;
  --danger-text:#991b1b;
  --border:#e2e8f0;
  --border-focus:#818cf8;
  --shadow-sm:0 1px 3px rgba(0,0,0,0.06);
  --shadow-md:0 4px 12px rgba(0,0,0,0.07);
  --shadow-lg:0 8px 24px rgba(0,0,0,0.09);
  --radius-sm:6px;
  --radius-md:10px;
  --radius-lg:14px;
}
body{
  font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;
  background:var(--bg-primary);
  color:var(--text-main);
  min-height:100vh;
  line-height:1.5;
}
.app-header{
  background:#1e1b4b;
  color:#fff;
  padding:24px 20px;
  border-bottom:3px solid var(--primary);
  box-shadow:0 4px 16px rgba(15,23,42,0.15);
}
.header-container{
  max-width:1200px;
  margin:0 auto;
  display:flex;
  flex-direction:column;
  gap:16px;
}
.header-top{
  display:flex;
  justify-content:space-between;
  align-items:flex-start;
  flex-wrap:wrap;
  gap:12px;
}
.badge-group{
  display:flex;
  align-items:center;
  gap:8px;
  flex-wrap:wrap;
}
.badge-chip{
  background:rgba(255,255,255,0.12);
  color:#e0e7ff;
  font-size:0.72rem;
  font-weight:600;
  padding:4px 10px;
  border-radius:20px;
  border:1px solid rgba(255,255,255,0.18);
  letter-spacing:.03em;
}
.feature-title{
  font-size:1.85rem;
  font-weight:800;
  letter-spacing:-0.02em;
  color:#ffffff;
  margin-bottom:4px;
}
.feature-subtitle{
  font-size:0.92rem;
  color:#c7d2fe;
  max-width:860px;
  line-height:1.55;
}
.stats-grid{
  display:grid;
  grid-template-columns:repeat(auto-fit, minmax(200px, 1fr));
  gap:12px;
  margin-top:8px;
}
.stat-card{
  background:rgba(255,255,255,0.07);
  border:1px solid rgba(255,255,255,0.12);
  border-radius:var(--radius-md);
  padding:14px 16px;
  display:flex;
  flex-direction:column;
  gap:2px;
  transition:background .2s;
}
.stat-card:hover{
  background:rgba(255,255,255,0.12);
}
.stat-val{
  font-size:1.55rem;
  font-weight:800;
  color:#ffffff;
  line-height:1.2;
}
.stat-label{
  font-size:0.72rem;
  font-weight:600;
  color:#a5b4fc;
  text-transform:uppercase;
  letter-spacing:.06em;
}
.nav-bar-wrap{
  background:#ffffff;
  border-bottom:1px solid var(--border);
  position:sticky;
  top:0;
  z-index:100;
  box-shadow:var(--shadow-sm);
}
.nav-bar{
  max-width:1200px;
  margin:0 auto;
  padding:0 20px;
  display:flex;
  align-items:center;
  justify-content:space-between;
  gap:16px;
  overflow-x:auto;
}
.tab-list{
  display:flex;
  gap:4px;
  list-style:none;
  padding:8px 0;
}
.tab-btn{
  background:none;
  border:none;
  padding:9px 16px;
  border-radius:var(--radius-sm);
  font-size:0.84rem;
  font-weight:600;
  color:var(--text-muted);
  cursor:pointer;
  display:flex;
  align-items:center;
  gap:8px;
  transition:all .15s;
  white-space:nowrap;
}
.tab-btn:hover{
  background:var(--bg-subtle);
  color:var(--text-main);
}
.tab-btn.active{
  background:var(--primary-subtle);
  color:var(--primary);
  box-shadow:inset 0 -2px 0 var(--primary);
}
.tab-count{
  font-size:0.7rem;
  background:var(--border);
  color:var(--text-muted);
  padding:2px 7px;
  border-radius:10px;
  font-weight:700;
}
.tab-btn.active .tab-count{
  background:var(--primary-light);
  color:var(--primary);
}
.search-box{
  position:relative;
  display:flex;
  align-items:center;
}
.search-input{
  padding:7px 12px 7px 30px;
  font-size:0.82rem;
  border:1.5px solid var(--border);
  border-radius:20px;
  width:220px;
  background:var(--bg-subtle);
  outline:none;
  transition:all .2s;
}
.search-input:focus{
  border-color:var(--border-focus);
  background:#fff;
  box-shadow:0 0 0 3px rgba(99,102,241,0.15);
  width:260px;
}
.search-icon{
  position:absolute;
  left:10px;
  font-size:0.8rem;
  color:var(--text-subtle);
  pointer-events:none;
}
.main-container{
  max-width:1200px;
  margin:0 auto;
  padding:24px 20px 60px;
  display:flex;
  flex-direction:column;
  gap:20px;
}
.tab-panel{
  display:none;
  flex-direction:column;
  gap:20px;
}
.tab-panel.active{
  display:flex;
}
.card{
  background:var(--bg-card);
  border-radius:var(--radius-lg);
  padding:22px 24px;
  box-shadow:var(--shadow-sm);
  border:1px solid var(--border);
}
.card-header-row{
  display:flex;
  align-items:center;
  justify-content:space-between;
  margin-bottom:16px;
  flex-wrap:wrap;
  gap:10px;
}
.card-title{
  font-size:1.08rem;
  font-weight:800;
  color:var(--text-main);
  display:flex;
  align-items:center;
  gap:8px;
}
.card-subtitle{
  font-size:0.82rem;
  color:var(--text-muted);
  margin-top:2px;
}
.topology-box{
  background:#0f172a;
  border-radius:var(--radius-md);
  padding:22px;
  color:#f8fafc;
  margin-bottom:8px;
}
.topology-header{
  display:flex;
  justify-content:space-between;
  align-items:center;
  margin-bottom:16px;
  flex-wrap:wrap;
  gap:8px;
}
.topology-title{
  font-size:0.82rem;
  font-weight:700;
  color:#a5b4fc;
  text-transform:uppercase;
  letter-spacing:.08em;
}
.topology-grid{
  display:flex;
  align-items:stretch;
  gap:12px;
  overflow-x:auto;
  padding:4px 2px 14px;
}
.service-node{
  background:#1e293b;
  border:1.5px solid #334155;
  border-radius:var(--radius-md);
  padding:16px;
  min-width:260px;
  display:flex;
  flex-direction:column;
  gap:10px;
  flex:1;
  position:relative;
  transition:border-color .2s,background .2s;
}
.service-node:hover{
  border-color:var(--primary);
  background:#24234d;
}
.service-node-header{
  display:flex;
  align-items:center;
  justify-content:space-between;
  gap:8px;
}
.service-node-title{
  font-size:0.88rem;
  font-weight:700;
  color:#fff;
  font-family:'SFMono-Regular',Consolas,monospace;
  word-break:break-word;
}
.service-node-feature{
  font-size:0.68rem;
  color:#94a3b8;
  font-weight:600;
}
.service-node-stats{
  display:flex;
  gap:12px;
  font-size:0.75rem;
  color:#cbd5e1;
  padding:8px 0;
  border-top:1px solid rgba(255,255,255,0.08);
  border-bottom:1px solid rgba(255,255,255,0.08);
}
.service-node-stat{
  display:flex;
  flex-direction:column;
  gap:1px;
}
.service-node-stat-val{
  font-weight:700;
  color:#fff;
}
.service-node-stat-label{
  font-size:0.65rem;
  color:#94a3b8;
  text-transform:uppercase;
}
.service-node-btn{
  background:rgba(99,102,241,0.25);
  color:#e0e7ff;
  border:1px solid rgba(99,102,241,0.4);
  padding:6px 12px;
  border-radius:var(--radius-sm);
  font-size:0.75rem;
  font-weight:600;
  cursor:pointer;
  margin-top:auto;
  transition:all .15s;
  text-align:center;
}
.service-node-btn:hover{
  background:var(--primary);
  color:#fff;
}
.node-conn{
  display:flex;
  align-items:center;
  justify-content:center;
  color:#64748b;
  font-size:1.4rem;
  flex-shrink:0;
  padding:0 2px;
}
.matrix-table{
  width:100%;
  border-collapse:collapse;
  font-size:0.82rem;
}
.matrix-table th{
  text-align:left;
  padding:10px 14px;
  background:var(--bg-subtle);
  color:var(--text-muted);
  font-weight:700;
  border-bottom:2px solid var(--border);
  font-size:0.75rem;
  text-transform:uppercase;
  letter-spacing:.04em;
}
.matrix-table td{
  padding:11px 14px;
  border-bottom:1px solid var(--border);
  vertical-align:middle;
}
.matrix-table tr:hover td{
  background:#f8fafc;
}
.matrix-table tr:last-child td{
  border-bottom:none;
}
.scenario-link{
  font-weight:700;
  color:var(--text-main);
  text-decoration:none;
  cursor:pointer;
  display:flex;
  align-items:center;
  gap:6px;
}
.scenario-link:hover{
  color:var(--primary);
}
.service-pill{
  font-size:0.72rem;
  font-weight:700;
  font-family:monospace;
  padding:3px 8px;
  border-radius:6px;
  background:#eef2ff;
  color:#4338ca;
  border:1px solid #c7d2fe;
}
.category{
  display:inline-block;
  padding:2px 9px;
  border-radius:12px;
  font-size:0.68rem;
  font-weight:700;
  letter-spacing:.03em;
}
.cat-success{background:var(--success-light);color:var(--success-text)}
.cat-alternative{background:var(--warning-light);color:var(--warning-text)}
.mini-stage-bar{
  display:flex;
  gap:3px;
  align-items:center;
}
.mini-dot{
  width:10px;
  height:10px;
  border-radius:50%;
}
.mini-done{background:var(--primary)}
.mini-active{background:#fff;border:2px solid var(--primary)}
.mini-todo{background:#cbd5e1}
.view-btn{
  background:var(--primary-subtle);
  color:var(--primary);
  border:1px solid var(--primary-light);
  padding:4px 10px;
  border-radius:var(--radius-sm);
  font-size:0.73rem;
  font-weight:600;
  cursor:pointer;
  transition:all .15s;
}
.view-btn:hover{
  background:var(--primary);
  color:#fff;
  border-color:var(--primary);
}
.scenario-layout{
  display:grid;
  grid-template-columns:300px minmax(0,1fr);
  gap:20px;
  align-items:flex-start;
}
@media(max-width:960px){
  .scenario-layout{
    grid-template-columns:1fr;
  }
}
.scenario-sidebar{
  background:var(--bg-card);
  border-radius:var(--radius-lg);
  border:1px solid var(--border);
  padding:14px;
  display:flex;
  flex-direction:column;
  gap:8px;
  position:sticky;
  top:70px;
  box-shadow:var(--shadow-sm);
  min-width:0;
  overflow:hidden;
}
.sidebar-title{
  font-size:0.75rem;
  font-weight:700;
  color:var(--text-subtle);
  text-transform:uppercase;
  letter-spacing:.08em;
  padding:0 4px;
}
.scenario-nav-item{
  padding:10px 12px;
  border-radius:var(--radius-md);
  border:1.5px solid transparent;
  background:var(--bg-subtle);
  cursor:pointer;
  display:flex;
  flex-direction:column;
  gap:6px;
  transition:all .15s;
  text-decoration:none;
  color:inherit;
  min-width:0;
  overflow:hidden;
}
.scenario-nav-item:hover{
  border-color:var(--border-focus);
  background:#f0f4ff;
}
.scenario-nav-item.active{
  border-color:var(--primary);
  background:var(--primary-subtle);
  box-shadow:0 0 0 2px rgba(99,102,241,0.15);
}
.nav-item-header{
  display:flex;
  align-items:flex-start;
  justify-content:space-between;
  gap:8px;
  min-width:0;
}
.nav-item-title{
  font-size:0.78rem;
  font-weight:700;
  line-height:1.35;
  word-break:break-word;
  overflow-wrap:anywhere;
  min-width:0;
  flex:1;
}
.nav-item-header .category{
  flex-shrink:0;
  margin-top:1px;
}
.nav-item-sub{
  display:flex;
  align-items:center;
  gap:8px;
  font-size:0.7rem;
  color:var(--text-muted);
  min-width:0;
}
.scenario-content{
  display:flex;
  flex-direction:column;
  gap:16px;
  min-width:0;
}
.scenario-view{
  display:none;
  flex-direction:column;
  gap:16px;
  min-width:0;
}
.scenario-view.active{
  display:flex;
}
.scenario-header-card{
  border-left:5px solid var(--primary);
  min-width:0;
}
.scenario-header-top{
  display:flex;
  justify-content:space-between;
  align-items:flex-start;
  flex-wrap:wrap;
  gap:10px;
  margin-bottom:8px;
  min-width:0;
}
.scenario-heading{
  font-size:1.35rem;
  font-weight:800;
  color:var(--text-main);
  letter-spacing:-0.01em;
  word-break:break-word;
  overflow-wrap:anywhere;
  min-width:0;
  flex:1;
}
.scenario-meta-row{
  display:flex;
  align-items:center;
  gap:8px;
  flex-wrap:wrap;
  margin-bottom:10px;
}
.sync-link{
  font-size:0.72rem;
  font-weight:600;
  color:#4338ca;
  text-decoration:none;
  border:1px solid #c7d2fe;
  background:#eef2ff;
  border-radius:6px;
  padding:2px 8px;
}
.sync-link:hover{background:#e0e7ff}
.scenario-desc{
  color:var(--text-muted);
  font-size:0.88rem;
  line-height:1.65;
}
.section-title{
  font-size:0.75rem;
  font-weight:700;
  color:var(--text-subtle);
  text-transform:uppercase;
  letter-spacing:.08em;
  margin-bottom:14px;
}
.stage-track{
  display:flex;
  align-items:flex-start;
}
.stage-wrap{
  flex:1;
  display:flex;
  flex-direction:column;
  align-items:center;
  gap:6px;
  position:relative;
}
.stage-circle{
  width:32px;
  height:32px;
  border-radius:50%;
  display:flex;
  align-items:center;
  justify-content:center;
  font-size:0.74rem;
  font-weight:700;
  position:relative;
  z-index:1;
}
.s-done .stage-circle{background:var(--primary);color:#fff}
.s-active .stage-circle{background:#fff;border:2.5px solid var(--primary);color:var(--primary);box-shadow:0 0 0 4px var(--primary-light)}
.s-todo .stage-circle{background:var(--bg-subtle);border:2px solid #cbd5e1;color:var(--text-subtle)}
.stage-label{
  font-size:0.65rem;
  color:var(--text-muted);
  text-align:center;
  max-width:72px;
  line-height:1.3;
}
.stage-connector{
  flex:1;
  height:2px;
  margin-top:16px;
  align-self:flex-start;
}
.conn-done{background:var(--primary)}
.conn-todo{background:var(--border)}
.progress-summary-row{
  display:flex;
  gap:16px;
  margin-top:16px;
  padding-top:14px;
  border-top:1px solid var(--border);
  font-size:0.78rem;
  color:var(--text-muted);
  flex-wrap:wrap;
}
.progress-summary-item{
  display:flex;
  align-items:center;
  gap:6px;
}
.summary-count-badge{
  background:var(--bg-subtle);
  border:1px solid var(--border);
  font-weight:700;
  padding:2px 7px;
  border-radius:10px;
  color:var(--text-main);
}
.flow-hint{
  font-size:0.74rem;
  color:var(--text-subtle);
  margin-bottom:12px;
}
.flow-scroll{
  overflow-x:auto;
  padding-bottom:8px;
}
.flow-row{
  display:flex;
  align-items:flex-start;
  gap:0;
  min-width:max-content;
  padding:4px 2px 12px;
}
.flow-step{
  display:flex;
  flex-direction:column;
  align-items:center;
  gap:6px;
}
.step-num{
  font-size:0.65rem;
  font-weight:700;
  color:var(--primary);
  background:var(--primary-light);
  padding:1px 7px;
  border-radius:10px;
}
.flow-box{
  background:var(--bg-subtle);
  border:2px solid var(--border);
  border-radius:var(--radius-md);
  padding:10px 12px;
  width:155px;
  text-align:center;
  font-size:0.78rem;
  line-height:1.45;
  cursor:pointer;
  transition:all .15s;
  color:#334155;
}
.flow-box:hover{
  border-color:var(--border-focus);
  background:var(--primary-subtle);
  transform:translateY(-2px);
  box-shadow:var(--shadow-md);
}
.flow-box.active{
  border-color:var(--primary);
  background:var(--primary-light);
  box-shadow:0 0 0 3px rgba(99,102,241,.25);
  color:var(--text-main);
  font-weight:600;
}
.flow-arrow{
  display:flex;
  align-items:center;
  padding:0 6px;
  margin-top:28px;
  color:#a5b4fc;
  font-size:1.1rem;
  flex-shrink:0;
}
.data-table{
  width:100%;
  border-collapse:collapse;
  font-size:0.82rem;
}
.data-table th{
  text-align:left;
  padding:8px 14px;
  background:var(--bg-subtle);
  color:var(--text-muted);
  font-weight:600;
  border-bottom:2px solid var(--border);
}
.data-table td{
  padding:7px 14px;
  border-bottom:1px solid #f1f5f9;
  vertical-align:top;
}
.data-table tr:last-child td{
  border-bottom:none;
}
.data-table .section-row td{
  padding:10px 14px 4px;
  font-size:0.7rem;
  font-weight:700;
  color:var(--text-subtle);
  text-transform:uppercase;
  letter-spacing:.08em;
  background:var(--bg-subtle);
  border-bottom:1px solid var(--border);
}
code{
  background:var(--bg-primary);
  padding:2px 6px;
  border-radius:5px;
  font-family:'SFMono-Regular',Consolas,monospace;
  font-size:0.77rem;
  color:#0f172a;
}
.task-group{
  margin-bottom:20px;
}
.task-group:last-child{
  margin-bottom:0;
}
.group-label{
  font-size:0.7rem;
  font-weight:700;
  color:var(--text-subtle);
  text-transform:uppercase;
  letter-spacing:.1em;
  margin-bottom:8px;
  display:flex;
  align-items:center;
  gap:8px;
}
.group-label::after{
  content:'';
  flex:1;
  height:1px;
  background:var(--border);
}
details.task-card{
  border:1.5px solid var(--border);
  border-radius:8px;
  margin-bottom:6px;
  transition:border-color .15s,background .15s,box-shadow .15s;
  background:#fff;
}
details.task-card>summary{
  display:flex;
  gap:12px;
  padding:11px 14px;
  cursor:pointer;
  list-style:none;
  align-items:flex-start;
  user-select:none;
}
details.task-card>summary::-webkit-details-marker{display:none}
details.task-card>summary::marker{display:none}
details.task-card.highlighted{
  border-color:var(--primary);
  background:#f0f4ff;
  box-shadow:0 0 0 2px rgba(99,102,241,.18);
}
details.task-card[open]{
  border-color:var(--border-focus);
}
details.task-card[open]>summary{
  border-bottom:1px solid var(--border);
}
.expand-icon{
  margin-left:auto;
  font-size:0.72rem;
  color:var(--text-subtle);
  transition:transform .18s;
  flex-shrink:0;
  margin-top:5px;
  line-height:1;
}
details.task-card[open] .expand-icon{
  transform:rotate(180deg);
}
.task-detail{
  padding:12px 14px 14px 34px;
  display:flex;
  flex-direction:column;
  gap:10px;
}
.detail-section{
  display:flex;
  flex-direction:column;
  gap:4px;
}
.detail-label{
  font-size:0.65rem;
  font-weight:700;
  color:var(--text-subtle);
  text-transform:uppercase;
  letter-spacing:.07em;
}
.detail-pre{
  background:var(--bg-subtle);
  border:1px solid var(--border);
  border-radius:6px;
  padding:8px 10px;
  font-family:'SFMono-Regular',Consolas,monospace;
  font-size:0.74rem;
  color:#334155;
  white-space:pre-wrap;
  word-break:break-word;
  line-height:1.55;
  margin:0;
}
.assert-list{
  list-style:none;
  display:flex;
  flex-direction:column;
  gap:3px;
  padding:0;
  margin:0;
}
.assert-list li{
  font-family:'SFMono-Regular',Consolas,monospace;
  font-size:0.74rem;
  background:var(--bg-subtle);
  border:1px solid var(--border);
  border-radius:4px;
  padding:3px 8px;
  color:#334155;
}
.dep-tags{
  display:flex;
  flex-wrap:wrap;
  gap:4px;
}
.dep-tag{
  background:#f1f5f9;
  color:#475569;
  font-size:0.67rem;
  padding:2px 8px;
  border-radius:10px;
  font-family:monospace;
}
.target-path{
  font-family:'SFMono-Regular',Consolas,monospace;
  font-size:0.72rem;
  color:var(--primary);
  word-break:break-all;
  line-height:1.7;
}
.detail-text{
  font-size:0.8rem;
  color:var(--text-muted);
  line-height:1.55;
}
.dot{
  width:8px;
  height:8px;
  border-radius:50%;
  margin-top:6px;
  flex-shrink:0;
}
.dot-pending{background:#cbd5e1}
.dot-in_progress{background:#f59e0b}
.dot-done{background:#22c55e}
.dot-failed{background:#ef4444}
.task-body{
  flex:1;
  min-width:0;
}
.task-id{
  font-size:0.67rem;
  color:var(--text-subtle);
  font-family:monospace;
  margin-bottom:2px;
}
.task-title{
  font-size:0.84rem;
  font-weight:500;
  color:var(--text-main);
  margin-bottom:6px;
  line-height:1.4;
}
.tags{
  display:flex;
  flex-wrap:wrap;
  gap:5px;
}
.tag{
  font-size:0.63rem;
  font-weight:700;
  padding:1px 7px;
  border-radius:10px;
}
.t-unit-test{background:#ede9fe;color:#5b21b6}
.t-integration-test{background:#dbeafe;color:#1e40af}
.t-component-test{background:#fce7f3;color:#9d174d}
.t-code-task{background:#dcfce7;color:#166534}
.t-api-test{background:#ffedd5;color:#9a3412}
.t-env-setup{background:#f1f5f9;color:#475569}
.t-interface{background:#e0e7ff;color:#4338ca}
.e-low{background:#dcfce7;color:#166534}
.e-med,.e-medium{background:#fef9c3;color:#854d0e}
.e-high{background:#fee2e2;color:#991b1b}
.status-badge{background:#f1f5f9;color:#64748b}
.sync-tag{
  font-size:0.67rem;
  font-weight:700;
  color:#4338ca;
  background:#e0e7ff;
  border:1px solid #c7d2fe;
  border-radius:10px;
  padding:2px 8px;
  text-decoration:none;
}
.sync-tag:hover{background:#c7d2fe}
.ah-row{
  display:flex;
  align-items:flex-start;
  gap:10px;
  padding:10px 0;
  border-top:1px solid var(--border);
}
.cat-reject{background:var(--danger-light);color:var(--danger-text)}
.empty-note{
  color:var(--text-subtle);
  font-size:0.83rem;
  font-style:italic;
}
.fn-tree{
  padding:4px 0 8px;
  display:flex;
  flex-direction:column;
  gap:4px;
}
.fn-node{
  position:relative;
  display:inline-flex;
  align-items:center;
  gap:6px;
  padding:6px 10px;
  background:var(--bg-subtle);
  border:1.5px solid var(--border);
  border-radius:8px;
  font-size:0.82rem;
  font-weight:500;
  color:var(--text-main);
  cursor:pointer;
  transition:all .15s;
  user-select:none;
}
.fn-node:hover{
  border-color:var(--border-focus);
  background:#f0f4ff}
.fn-node.fn-root{background:#eef2ff;border-color:#a5b4fc;font-weight:700}
.fn-node.fn-active{border-color:var(--primary);background:#e0e7ff;box-shadow:0 0 0 3px rgba(99,102,241,.2)}
.fn-children{
  margin-left:20px;
  border-left:2px solid var(--border);
  padding-left:14px;
  margin-top:4px;
  display:flex;
  flex-direction:column;
  gap:4px;
}
.fn-name{font-family:'SFMono-Regular',Consolas,monospace;font-size:0.78rem}
.controls-row{
  display:flex;
  gap:8px;
  margin-bottom:12px;
}
.btn-secondary{
  background:var(--bg-subtle);
  border:1px solid var(--border);
  padding:5px 12px;
  border-radius:var(--radius-sm);
  font-size:0.75rem;
  font-weight:600;
  color:var(--text-muted);
  cursor:pointer;
  transition:all .15s;
}
.btn-secondary:hover{
  background:var(--border);
  color:var(--text-main);
}
"""

JS = """
function switchTab(tabId) {
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.tab === tabId);
  });
  document.querySelectorAll('.tab-panel').forEach(panel => {
    panel.classList.toggle('active', panel.id === 'panel-' + tabId);
  });
  window.location.hash = tabId;
}

function selectScenario(serviceKey, scenarioId) {
  switchTab(serviceKey);
  const servicePanel = document.getElementById('panel-' + serviceKey);
  if (!servicePanel) return;

  servicePanel.querySelectorAll('.scenario-nav-item').forEach(item => {
    item.classList.toggle('active', item.dataset.scenario === scenarioId);
  });
  servicePanel.querySelectorAll('.scenario-view').forEach(view => {
    view.classList.toggle('active', view.id === 'view-' + scenarioId);
  });

  window.location.hash = serviceKey + '/' + scenarioId;
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function activateStep(scenarioId, n) {
  const view = document.getElementById('view-' + scenarioId);
  if (!view) return;

  const box = view.querySelector('.flow-box[data-step="' + n + '"]');
  const isAlreadyActive = box && box.classList.contains('active');

  view.querySelectorAll('.flow-box').forEach(b => b.classList.remove('active'));
  view.querySelectorAll('details.task-card').forEach(c => c.classList.remove('highlighted'));

  if (isAlreadyActive) return;

  if (box) box.classList.add('active');

  view.querySelectorAll('details.task-card').forEach(card => {
    const s = card.dataset.step;
    if (s === 'all' || s === String(n) || s === (n < 10 ? '0' + n : String(n))) {
      card.classList.add('highlighted');
    }
  });

  const target = view.querySelector('details.task-card[data-step="' + n + '"], details.task-card[data-step="' + (n < 10 ? '0' + n : n) + '"]');
  if (target) {
    target.open = true;
    target.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }
}

function activateFn(el, taskIds, scenarioId) {
  const view = document.getElementById('view-' + scenarioId) || el.closest('.scenario-view');
  if (!view) return;

  const isAlreadyActive = el.classList.contains('fn-active');
  view.querySelectorAll('.fn-node').forEach(n => n.classList.remove('fn-active'));
  view.querySelectorAll('details.task-card').forEach(c => c.classList.remove('highlighted'));

  if (isAlreadyActive) return;

  el.classList.add('fn-active');
  taskIds.forEach(id => {
    view.querySelectorAll('.task-id').forEach(tid => {
      if (tid.textContent.trim() === id) {
        const card = tid.closest('details.task-card');
        if (card) {
          card.classList.add('highlighted');
          card.open = true;
        }
      }
    });
  });

  const first = view.querySelector('details.task-card.highlighted');
  if (first) first.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

function toggleAllTasks(scenarioId, expand) {
  const view = document.getElementById('view-' + scenarioId);
  if (!view) return;
  view.querySelectorAll('details.task-card').forEach(card => {
    card.open = expand;
  });
}

function filterScenarios(query) {
  const q = query.toLowerCase().trim();
  document.querySelectorAll('.matrix-row').forEach(row => {
    const text = row.textContent.toLowerCase();
    row.style.display = text.includes(q) ? '' : 'none';
  });
  document.querySelectorAll('.scenario-nav-item').forEach(item => {
    const text = item.textContent.toLowerCase();
    item.style.display = text.includes(q) ? '' : 'none';
  });
}

window.addEventListener('DOMContentLoaded', () => {
  const hash = window.location.hash.replace('#', '');
  if (hash) {
    if (hash.includes('/')) {
      const parts = hash.split('/');
      selectScenario(parts[0], parts[1]);
    } else {
      switchTab(hash);
    }
  }
});
"""


def parse_datatest(md_text):
    sections, cur = [], None
    for line in md_text.splitlines():
        if line.startswith("## "):
            cur = {"title": line[3:].strip(), "header": None, "rows": []}
            sections.append(cur)
        elif cur is not None and line.startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if cur["header"] is None:
                cur["header"] = cells
            elif not all(re.fullmatch(r":?-{3,}:?", c) for c in cells):
                cur["rows"].append(cells)
    return sections


def calculate_stage_states(meta, base, tasks_by_group):
    backlog = tasks_by_group.get("02-Backlog", [])
    api = tasks_by_group.get("03-Api-test", [])
    all_tasks = tasks_by_group.get("01-Setup", []) + backlog + api

    def all_done(task_list):
        return len(task_list) > 0 and all(
            t.get("status") == "done" for t in task_list
        )

    has_testdata = (base / "01-Testdata" / "Datatest.md").exists()
    return [
        True,  # 1: Requirement defined
        has_testdata,  # 2: Test data
        len(all_tasks) > 0,  # 3: Tasks created
        all_done(backlog),  # 4: Backlog executed
        all_done(api),  # 5: Api test executed
        bool(meta.get("accepted")),  # 6: Acceptance review
    ]


def stage_track_html(states):
    parts = []
    for i, (d, label) in enumerate(zip(states, STAGE_LABELS)):
        if i:
            parts.append(
                f'<div class="stage-connector conn-{"done" if states[i - 1] else "todo"}"></div>'
            )
        cls = (
            "s-done"
            if d
            else ("s-active" if i == 0 or states[i - 1] else "s-todo")
        )
        parts.append(
            f'<div class="stage-wrap {cls}">'
            f'<div class="stage-circle">{i + 1}</div>'
            f'<div class="stage-label">{label}</div>'
            f"</div>"
        )
    return "\n          ".join(parts)


def flow_boxes_html(scenario_id, steps):
    parts = []
    for i, s in enumerate(steps):
        if i:
            parts.append('<div class="flow-arrow">→</div>')
        parts.append(
            f'<div class="flow-step">'
            f'<div class="step-num">{i + 1}</div>'
            f'<div class="flow-box" data-step="{i + 1}" onclick="activateStep(\'{esc(scenario_id)}\', {i + 1})">{esc(s)}</div>'
            f"</div>"
        )
    return "\n            ".join(parts)


def datatest_html(sections):
    if not sections:
        return '<p class="empty-note">Test data not yet created.</p>'
    cols = len(sections[0]["header"])
    parts = []
    for s in sections:
        parts.append(
            f'<tr class="section-row"><td colspan="{cols}">{esc(s["title"])}</td></tr>'
        )
        for row in s["rows"]:
            tds = []
            for c in row:
                if re.fullmatch(r"[0-9_\-]+", c) or c.startswith(
                    ("EAA-", "acct-", "1000")
                ):
                    tds.append(f"<td><code>{esc(c)}</code></td>")
                else:
                    tds.append(f"<td>{esc(c)}</td>")
            parts.append("<tr>" + "".join(tds) + "</tr>")
    header = "".join(f"<th>{esc(h)}</th>" for h in sections[0]["header"])
    return (
        f'<table class="data-table"><thead><tr>{header}</tr></thead><tbody>'
        + "".join(parts)
        + "</tbody></table>"
    )


def task_card_html(t, step):
    status = t.get("status", "pending")
    dot = {
        "pending": "dot-pending",
        "in_progress": "dot-in_progress",
        "done": "dot-done",
        "failed": "dot-failed",
    }.get(status, "dot-pending")
    type_cls = TYPE_TAGS.get(t.get("type", ""), "t-env-setup")
    eff = t.get("effort", "low")
    detail = []

    if t.get("contract"):
        detail.append(
            f'<div class="detail-section"><div class="detail-label">Contract</div><pre class="detail-pre">{esc(t["contract"])}</pre></div>'
        )
    if t.get("pseudocode"):
        detail.append(
            f'<div class="detail-section"><div class="detail-label">Pseudocode</div><pre class="detail-pre">{esc(t["pseudocode"])}</pre></div>'
        )
    if t.get("cases"):
        items = "".join(
            f'<li>{esc(c.get("given", ""))} → {esc("; ".join(c.get("assert", [])))}</li>'
            for c in t["cases"]
        )
        detail.append(
            f'<div class="detail-section"><div class="detail-label">Cases</div><ul class="assert-list">{items}</ul></div>'
        )
    if t.get("uses"):
        detail.append(
            f'<div class="detail-section"><div class="detail-label">Test data</div><div class="detail-text">{esc(json.dumps(t["uses"], ensure_ascii=False))}</div></div>'
        )
    if t.get("depends_on"):
        detail.append(
            f'<div class="detail-section"><div class="detail-label">Depends on</div><div class="dep-tags">'
            + "".join(f'<span class="dep-tag">{esc(d)}</span>' for d in t["depends_on"])
            + "</div></div>"
        )
    if t.get("targets"):
        detail.append(
            '<div class="detail-section"><div class="detail-label">Targets</div>'
            + "".join(
                f'<div class="target-path">{esc(x.get("path", ""))} ({esc(x.get("mode", "modify"))})</div>'
                for x in t["targets"]
            )
            + "</div>"
        )
    if t.get("command"):
        detail.append(
            f'<div class="detail-section"><div class="detail-label">Command</div><div class="detail-text">{esc(t["command"])}</div></div>'
        )
    if t.get("acceptance"):
        detail.append(
            f'<div class="detail-section"><div class="detail-label">Acceptance</div><div class="detail-text">{esc(t["acceptance"])}</div></div>'
        )
    if t.get("notes"):
        detail.append(
            f'<div class="detail-section"><div class="detail-label">Notes</div><div class="detail-text">{esc(t["notes"])}</div></div>'
        )

    detail_html = (
        "".join(detail) if detail else '<div class="detail-text">(no extra detail)</div>'
    )
    sync_tag = ""
    if t.get("sync"):
        sync_tag = f'<a class="tag sync-tag" href="{esc(t["sync"].get("url", "#"))}" target="_blank">↗ #{esc(str(t["sync"].get("id", "")))}</a>'

    return (
        f'<details class="task-card" data-step="{step}">\n'
        f"  <summary>\n"
        f'    <div class="dot {dot}"></div>\n'
        f'    <div class="task-body">\n'
        f'      <div class="task-id">{esc(t["id"])}</div>\n'
        f'      <div class="task-title">{esc(t.get("title", ""))}</div>\n'
        f'      <div class="tags">\n'
        f'        <span class="tag {type_cls}">{esc(t.get("type", ""))}</span>\n'
        f'        <span class="tag e-{eff}">{esc(eff)}</span>\n'
        f'        <span class="tag status-badge">{esc(status)}</span>{sync_tag}\n'
        f"      </div>\n"
        f"    </div>\n"
        f'    <span class="expand-icon">▾</span>\n'
        f"  </summary>\n"
        f'  <div class="task-detail">{detail_html}</div>\n'
        f"</details>"
    )


def tasks_html(tasks_by_group):
    all_empty = all(len(v) == 0 for v in tasks_by_group.values())
    if all_empty:
        return '<p class="empty-note">Tasks not yet created (Stage 3).</p>'

    out = []
    for group_key, label in [
        ("01-Setup", "Setup"),
        ("02-Backlog", "Backlog"),
        ("03-Api-test", "Api Test"),
    ]:
        tasks = tasks_by_group.get(group_key, [])
        out.append(f'<div class="task-group"><div class="group-label">{label}</div>')
        if not tasks:
            out.append('<p class="empty-note">—</p>')
        else:
            for t in tasks:
                step = "all"
                if group_key == "03-Api-test":
                    m = re.match(r"(\d+)-", t["id"])
                    step = m.group(1) if m else "all"
                out.append(task_card_html(t, step))
        out.append("</div>")
    return "\n    ".join(out)


def fn_tree_html(sc_dir, scenario_id):
    hp = sc_dir / "scenario.html"
    if hp.exists():
        content = hp.read_text(encoding="utf-8")
        m = re.search(
            r'<div class="fn-tree">(.*?)</div>\s*<div style="display:flex;align-items:center;gap:10px;margin-top:14px">',
            content,
            re.S,
        )
        if m:
            tree_inner = m.group(1).strip()
            # Rewrite activateFn call signatures to include scenarioId
            tree_inner = re.sub(
                r'activateFn\(this,\s*(\[.*?\])\)',
                rf"activateFn(this, \1, '{scenario_id}')",
                tree_inner,
            )
            return f'<div class="fn-tree">{tree_inner}</div>'
    return '<p class="empty-note">Functional design tree not yet created.</p>'


def acceptance_html(meta):
    rounds = meta.get("acceptanceHistory") or []
    if not rounds:
        return '<p class="empty-note">No acceptance rounds recorded yet.</p>'
    rows = []
    for r in rounds:
        cls = "cat-success" if r.get("result") == "accepted" else "cat-reject"
        rows.append(
            f'<div class="ah-row">'
            f'<span class="category {cls}" style="flex-shrink:0;margin-bottom:0">Round {r.get("round")} · {r.get("result")}</span>'
            f'<p class="desc" style="margin:0;font-size:0.84rem">{esc(r.get("feedback", ""))}</p>'
            f"</div>"
        )
    return "".join(rows)


def scan_feature_scenarios(services_dir, feature_keyword):
    scenarios = []
    svc_dir = Path(services_dir)
    if not svc_dir.exists():
        raise SystemExit(f"Services directory does not exist: {services_dir}")

    is_all = feature_keyword.upper() == "ALL"

    # Scan all service folders
    for service_path in sorted(svc_dir.iterdir()):
        if not service_path.is_dir():
            continue

        scenario_root = service_path / "work" / "Scenario"
        if not scenario_root.exists():
            continue

        for sc_html in sorted(scenario_root.rglob("scenario.html")):
            sc_dir = sc_html.parent
            feature_dir_name = ""
            for part in sc_html.parts:
                if is_all:
                    if part not in ("work", "Scenario", "Success", "Alternative", "scenario.html", service_path.name):
                        feature_dir_name = part
                elif feature_keyword.upper() in part.upper():
                    feature_dir_name = part
                    break

            # Read scenario-meta
            text = sc_html.read_text(encoding="utf-8")
            m = re.search(
                r'<script id="scenario-meta" type="application/json">(.*?)</script>',
                text,
                re.S,
            )
            if not m and not is_all and not feature_dir_name:
                continue

            meta = json.loads(m.group(1)) if m else {}
            sc_name = meta.get("scenario", sc_dir.name)

            # Match on feature name or folder name or scenario name
            if not is_all:
                if not (
                    feature_keyword.upper() in feature_dir_name.upper()
                    or feature_keyword.upper() in sc_dir.name.upper()
                    or feature_keyword.upper() in sc_name.upper()
                ):
                    continue

            # Load tasks
            tdir = sc_dir / "02-Task"
            tasks_by_group = {
                "01-Setup": [],
                "02-Backlog": [],
                "03-Api-test": [],
            }
            if tdir.exists():
                for grp in ["01-Setup", "02-Backlog", "03-Api-test"]:
                    gpath = tdir / grp
                    if gpath.exists():
                        for f in sorted(gpath.glob("*.json")):
                            try:
                                tasks_by_group[grp].append(
                                    json.loads(f.read_text(encoding="utf-8"))
                                )
                            except Exception:
                                pass

            # Load test data
            dt_file = sc_dir / "01-Testdata" / "Datatest.md"
            testdata_sections = (
                parse_datatest(dt_file.read_text(encoding="utf-8"))
                if dt_file.exists()
                else []
            )

            stage_states = calculate_stage_states(meta, sc_dir, tasks_by_group)

            category = meta.get("category") or (
                "Success" if "Success" in str(sc_dir) else "Alternative"
            )

            scenarios.append(
                {
                    "service": service_path.name,
                    "service_path": str(service_path),
                    "feature": feature_dir_name or feature_keyword,
                    "category": category,
                    "id": sc_name,
                    "scenario": sc_name,
                    "dir_path": sc_dir,
                    "meta": meta,
                    "tasks_by_group": tasks_by_group,
                    "testdata_sections": testdata_sections,
                    "stage_states": stage_states,
                    "stages_done": sum(1 for s in stage_states if s),
                    "total_tasks": sum(
                        len(v) for v in tasks_by_group.values()
                    ),
                    "done_tasks": sum(
                        sum(1 for t in v if t.get("status") == "done")
                        for v in tasks_by_group.values()
                    ),
                    "accepted": bool(meta.get("accepted")),
                }
            )

    return scenarios


def render_feature_dashboard(scenarios, feature_name, title=None, subtitle=None):
    # Group by service
    services = {}
    for sc in scenarios:
        s_name = sc["service"]
        if s_name not in services:
            services[s_name] = []
        services[s_name].append(sc)

    total_scenarios = len(scenarios)
    total_tasks = sum(sc["total_tasks"] for sc in scenarios)
    total_done_tasks = sum(sc["done_tasks"] for sc in scenarios)
    total_accepted = sum(1 for sc in scenarios if sc["accepted"])
    total_services = len(services)

    service_names_str = ", ".join(sorted(services.keys()))

    if not title:
        f_display = feature_name.replace("_", " ").title() if feature_name != "ALL" else "All Features"
        title = f"{f_display} Cross-Service Dashboard"

    if not subtitle:
        subtitle = (
            f"Cross-service blueprint across {total_services} microservices ({service_names_str}) "
            f"aggregating {total_scenarios} scenarios and {total_tasks} tasks."
        )

    # 1. Topology & Service Cards (Dynamic in Overview)
    topology_cards = []
    for s_idx, (s_name, sc_list) in enumerate(services.items()):
        if s_idx > 0:
            topology_cards.append('<div class="node-conn">➔</div>')
        
        s_tasks = sum(sc["total_tasks"] for sc in sc_list)
        s_done_tasks = sum(sc["done_tasks"] for sc in sc_list)
        s_accepted = sum(1 for sc in sc_list if sc["accepted"])
        s_features = sorted(list(set(sc["feature"] for sc in sc_list)))
        feature_tag = s_features[0] if s_features else "Feature"

        topology_cards.append(
            f'<div class="service-node">'
            f'  <div class="service-node-header">'
            f'    <div class="service-node-title">{esc(s_name)}</div>'
            f'    <span class="service-pill">{len(sc_list)} scenarios</span>'
            f"  </div>"
            f'  <div class="service-node-feature">Feature: {esc(feature_tag)}</div>'
            f'  <div class="service-node-stats">'
            f'    <div class="service-node-stat">'
            f'      <span class="service-node-stat-val">{s_done_tasks} / {s_tasks}</span>'
            f'      <span class="service-node-stat-label">Tasks Done</span>'
            f"    </div>"
            f'    <div class="service-node-stat">'
            f'      <span class="service-node-stat-val">{s_accepted} / {len(sc_list)}</span>'
            f'      <span class="service-node-stat-label">Accepted</span>'
            f"    </div>"
            f"  </div>"
            f'  <button class="service-node-btn" onclick="switchTab(\'{esc(s_name)}\')">Browse Scenarios →</button>'
            f"</div>"
        )

    # 2. Overview Matrix Table
    matrix_rows = []
    for sc in scenarios:
        cat_cls = (
            "cat-success"
            if sc["category"].lower() == "success"
            else "cat-alternative"
        )
        service_key = sc["service"]
        sc_id = sc["id"]

        mini_dots = "".join(
            f'<div class="mini-dot {"mini-done" if s else "mini-todo"}"></div>'
            for s in sc["stage_states"]
        )

        matrix_rows.append(
            f'<tr class="matrix-row">'
            f'<td><span class="service-pill">{esc(sc["service"])}</span></td>'
            f'<td><span class="category {cat_cls}">{esc(sc["category"])}</span></td>'
            f'<td><a class="scenario-link" onclick="selectScenario(\'{esc(service_key)}\', \'{esc(sc_id)}\')">{esc(sc["scenario"])}</a></td>'
            f'<td><div class="mini-stage-bar">{mini_dots} <span style="font-size:0.75rem;margin-left:6px;font-weight:700">{sc["stages_done"]}/6</span></div></td>'
            f'<td><span class="summary-count-badge">{sc["done_tasks"]}/{sc["total_tasks"]} done</span></td>'
            f'<td>{"<span class=\'category cat-success\'>Accepted</span>" if sc["accepted"] else "<span class=\'category cat-alternative\'>In Progress</span>"}</td>'
            f'<td><button class="view-btn" onclick="selectScenario(\'{esc(service_key)}\', \'{esc(sc_id)}\')">View →</button></td>'
            f"</tr>"
        )

    # 3. Service Tab Panels
    service_panels = []
    tab_buttons = [
        '<button class="tab-btn active" data-tab="overview" onclick="switchTab(\'overview\')">'
        '📊 Feature Overview <span class="tab-count">'
        + str(total_scenarios)
        + "</span></button>"
    ]

    for s_name, sc_list in services.items():
        tab_buttons.append(
            f'<button class="tab-btn" data-tab="{esc(s_name)}" onclick="switchTab(\'{esc(s_name)}\')">'
            f'📦 {esc(s_name)} <span class="tab-count">{len(sc_list)}</span>'
            f"</button>"
        )

        nav_items = []
        scenario_views = []

        for idx, sc in enumerate(sc_list):
            is_first = idx == 0
            active_cls = "active" if is_first else ""
            cat_cls = (
                "cat-success"
                if sc["category"].lower() == "success"
                else "cat-alternative"
            )
            sc_id = sc["id"]

            nav_items.append(
                f'<div class="scenario-nav-item {active_cls}" data-scenario="{esc(sc_id)}" onclick="selectScenario(\'{esc(s_name)}\', \'{esc(sc_id)}\')">'
                f'  <div class="nav-item-header">'
                f'    <span class="nav-item-title">{esc(sc["scenario"])}</span>'
                f'    <span class="category {cat_cls}">{esc(sc["category"])}</span>'
                f"  </div>"
                f'  <div class="nav-item-sub">'
                f'    <span>Stage {sc["stages_done"]}/6</span>'
                f'    <span>•</span>'
                f'    <span>{sc["total_tasks"]} tasks</span>'
                f"  </div>"
                f"</div>"
            )

            # Render scenario content
            meta = sc["meta"]
            tasks_by_group = sc["tasks_by_group"]
            setup_c = len(tasks_by_group.get("01-Setup", []))
            setup_d = sum(
                1
                for t in tasks_by_group.get("01-Setup", [])
                if t.get("status") == "done"
            )
            backlog_c = len(tasks_by_group.get("02-Backlog", []))
            backlog_d = sum(
                1
                for t in tasks_by_group.get("02-Backlog", [])
                if t.get("status") == "done"
            )
            api_c = len(tasks_by_group.get("03-Api-test", []))
            api_d = sum(
                1
                for t in tasks_by_group.get("03-Api-test", [])
                if t.get("status") == "done"
            )

            sync_link_html = ""
            if meta.get("sync"):
                sync_link_html = f'<a class="sync-link" href="{esc(meta["sync"].get("url", "#"))}" target="_blank">↗ Issue #{esc(str(meta["sync"].get("id", "")))}</a>'

            scenario_views.append(
                f'<div class="scenario-view {active_cls}" id="view-{esc(sc_id)}">'
                f'  <div class="card scenario-header-card">'
                f'    <div class="scenario-header-top">'
                f'      <div class="scenario-heading">{esc(sc["scenario"])}</div>'
                f'      <div class="badge-group">'
                f'        <span class="service-pill">{esc(s_name)}</span>'
                f'        <span class="category {cat_cls}">{esc(sc["category"])}</span>'
                f"        {sync_link_html}"
                f"      </div>"
                f"    </div>"
                f'    <p class="scenario-desc">{esc(meta.get("description", ""))}</p>'
                f"  </div>"
                f'  <div class="card">'
                f'    <div class="section-title">6-Stage Progress Indicator</div>'
                f'    <div class="stage-track">'
                f"      {stage_track_html(sc['stage_states'])}"
                f"    </div>"
                f'    <div class="progress-summary-row">'
                f'      <div class="progress-summary-item">Setup: <span class="summary-count-badge">{setup_d}/{setup_c} done</span></div>'
                f'      <div class="progress-summary-item">Backlog: <span class="summary-count-badge">{backlog_d}/{backlog_c} done</span></div>'
                f'      <div class="progress-summary-item">Api Test: <span class="summary-count-badge">{api_d}/{api_c} done</span></div>'
                f"    </div>"
                f"  </div>"
                f'  <div class="card">'
                f'    <div class="section-title">E2E Flow</div>'
                f'    <div class="flow-hint">Click a step to highlight matching task cards.</div>'
                f'    <div class="flow-scroll">'
                f'      <div class="flow-row">'
                f"        {flow_boxes_html(sc_id, meta.get('steps', []))}"
                f"      </div>"
                f"    </div>"
                f"  </div>"
                f'  <div class="card">'
                f'    <div class="section-title">Functional Design</div>'
                f"    {fn_tree_html(sc['dir_path'], sc_id)}"
                f"  </div>"
                f'  <div class="card">'
                f'    <div class="section-title">Test Data</div>'
                f"    {datatest_html(sc['testdata_sections'])}"
                f"  </div>"
                f'  <div class="card">'
                f'    <div class="card-header-row">'
                f'      <div class="section-title" style="margin-bottom:0">Tasks ({sc["total_tasks"]})</div>'
                f'      <div class="controls-row">'
                f'        <button class="btn-secondary" onclick="toggleAllTasks(\'{esc(sc_id)}\', true)">Expand All</button>'
                f'        <button class="btn-secondary" onclick="toggleAllTasks(\'{esc(sc_id)}\', false)">Collapse All</button>'
                f"      </div>"
                f"    </div>"
                f"    {tasks_html(tasks_by_group)}"
                f"  </div>"
                f'  <div class="card">'
                f'    <div class="section-title">Acceptance Review History</div>'
                f"    {acceptance_html(meta)}"
                f"  </div>"
                f"</div>"
            )

        service_panels.append(
            f'<div class="tab-panel" id="panel-{esc(s_name)}">'
            f'  <div class="scenario-layout">'
            f'    <div class="scenario-sidebar">'
            f'      <div class="sidebar-title">Scenarios ({len(sc_list)})</div>'
            f"      {''.join(nav_items)}"
            f"    </div>"
            f'    <div class="scenario-content">'
            f"      {''.join(scenario_views)}"
            f"    </div>"
            f"  </div>"
            f"</div>"
        )

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<style>
{CSS}
</style>
</head>
<body>

<header class="app-header">
  <div class="header-container">
    <div class="header-top">
      <div>
        <div class="feature-title">⚡ {esc(title)}</div>
        <p class="feature-subtitle">{esc(subtitle)}</p>
      </div>
      <div class="badge-group">
        <span class="badge-chip">RAT Workspace</span>
        <span class="badge-chip">Feature: {esc(feature_name)}</span>
        <span class="badge-chip">Live Report</span>
      </div>
    </div>
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-val">{total_services}</div>
        <div class="stat-label">Services</div>
      </div>
      <div class="stat-card">
        <div class="stat-val">{total_scenarios}</div>
        <div class="stat-label">Total Scenarios</div>
      </div>
      <div class="stat-card">
        <div class="stat-val">{total_done_tasks} / {total_tasks}</div>
        <div class="stat-label">Tasks Done</div>
      </div>
      <div class="stat-card">
        <div class="stat-val">{total_accepted} / {total_scenarios}</div>
        <div class="stat-label">Accepted Scenarios</div>
      </div>
    </div>
  </div>
</header>

<div class="nav-bar-wrap">
  <div class="nav-bar">
    <ul class="tab-list">
      {''.join(tab_buttons)}
    </ul>
    <div class="search-box">
      <span class="search-icon">🔍</span>
      <input type="text" class="search-input" placeholder="Search scenarios..." oninput="filterScenarios(this.value)">
    </div>
  </div>
</div>

<main class="main-container">

  <!-- Overview Panel -->
  <div class="tab-panel active" id="panel-overview">
    
    <!-- Cross-Service Participating Topology -->
    <div class="topology-box">
      <div class="topology-header">
        <div class="topology-title">Participating Microservices & Architecture Topology</div>
        <span class="badge-chip">{total_services} Active Services</span>
      </div>
      <div class="topology-grid">
        {''.join(topology_cards)}
      </div>
    </div>

    <!-- Scenario Matrix -->
    <div class="card">
      <div class="card-header-row">
        <div>
          <div class="card-title">Cross-Service Scenarios Matrix</div>
          <div class="card-subtitle">Complete scenario ledger across all participating microservices</div>
        </div>
      </div>
      <table class="matrix-table">
        <thead>
          <tr>
            <th>Service</th>
            <th>Category</th>
            <th>Scenario</th>
            <th>6-Stage Progress</th>
            <th>Tasks</th>
            <th>Status</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          {''.join(matrix_rows)}
        </tbody>
      </table>
    </div>

  </div>

  <!-- Service Specific Panels -->
  {''.join(service_panels)}

</main>

<script>
{JS}
</script>

</body>
</html>
"""
    return html_content


def verify_balanced_tags(html_str):
    from html.parser import HTMLParser

    class TagValidator(HTMLParser):
        def __init__(self):
            super().__init__()
            self.stack = []
            self.errors = []

        def handle_starttag(self, tag, attrs):
            if tag.lower() not in VOID_TAGS:
                self.stack.append((tag.lower(), self.getpos()))

        def handle_endtag(self, tag):
            tag_l = tag.lower()
            if tag_l in VOID_TAGS:
                return
            if not self.stack:
                self.errors.append(f"unexpected </{tag_l}> at {self.getpos()}")
                return
            top, pos = self.stack.pop()
            if top != tag_l:
                self.errors.append(
                    f"mismatched </{tag_l}> at {self.getpos()} (expected </{top}> opened at {pos})"
                )

    parser = TagValidator()
    parser.feed(html_str)
    parser.close()
    return len(parser.errors) == 0 and len(parser.stack) == 0, parser.errors, parser.stack


def find_default_services_dir():
    """Auto-detect the services root directory from env, cwd, or parent hierarchy."""
    if "SERVICES_DIR" in os.environ:
        return Path(os.environ["SERVICES_DIR"]).resolve()

    cwd = Path.cwd().resolve()
    candidates = [
        cwd / "services",
        cwd.parent / "services",
        cwd.parent.parent / "services",
        cwd.parent.parent.parent / "services",
        cwd.parent.parent.parent.parent / "services",
        Path("/Users/jackmod/Develops/services"),
        cwd,
    ]
    for c in candidates:
        if c.is_dir() and any(
            (c / repo / "work").exists() or (c / repo / "trust-me-bro-ai").exists()
            for repo in os.listdir(c)
            if (c / repo).is_dir()
        ):
            return c
    return cwd


def get_scenarios_fingerprint(services_dir):
    """Compute a timestamp fingerprint of all scenario files under services_dir."""
    svc_dir = Path(services_dir)
    if not svc_dir.exists():
        return 0
    max_mtime = 0
    for sc_root in svc_dir.glob("*/work/Scenario"):
        for p in sc_root.rglob("*"):
            if p.is_file() and p.suffix in (".json", ".md", ".html"):
                try:
                    m = p.stat().st_mtime
                    if m > max_mtime:
                        max_mtime = m
                except OSError:
                    pass
    return max_mtime


def run_serve(args, out_path, port=8080):
    """Run zero-dependency local HTTP server with automatic live-reload on file changes."""
    import time
    import threading
    from http.server import HTTPServer, BaseHTTPRequestHandler

    state = {
        "html": "",
        "version": str(time.time()),
    }

    def update_dashboard():
        scenarios = scan_feature_scenarios(args.services_dir, args.feature)
        if not scenarios:
            return
        raw_html = render_feature_dashboard(scenarios, args.feature, title=args.title)
        # Inject live-reload client
        live_reload_script = """
<script>
(function() {
  let _currentVer = null;
  setInterval(async function() {
    try {
      const res = await fetch('/live-reload-version');
      const ver = await res.text();
      if (_currentVer === null) {
        _currentVer = ver;
      } else if (_currentVer !== ver) {
        _currentVer = ver;
        console.log('[live-reload] Scenario files updated, reloading...');
        window.location.reload();
      }
    } catch(e) {}
  }, 800);
})();
</script>
</body>"""
        state["html"] = raw_html.replace("</body>", live_reload_script)
        state["version"] = str(time.time())
        # Also write to disk if out_path is set
        if out_path:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(raw_html, encoding="utf-8")

    update_dashboard()

    # Watcher thread
    def watch_loop():
        last_fp = get_scenarios_fingerprint(args.services_dir)
        while True:
            time.sleep(0.8)
            curr_fp = get_scenarios_fingerprint(args.services_dir)
            if curr_fp > last_fp:
                last_fp = curr_fp
                print(f"[live-reload] File change detected at {time.strftime('%H:%M:%S')}, regenerating...")
                update_dashboard()

    watcher = threading.Thread(target=watch_loop, daemon=True)
    watcher.start()

    class DashboardHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/live-reload-version":
                self.send_response(200)
                self.send_header("Content-Type", "text/plain")
                self.send_header("Cache-Control", "no-cache")
                self.end_headers()
                self.wfile.write(state["version"].encode("utf-8"))
            else:
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Cache-Control", "no-cache")
                self.end_headers()
                self.wfile.write(state["html"].encode("utf-8"))

        def log_message(self, format, *log_args):
            pass  # Suppress request spam

    server = HTTPServer(("127.0.0.1", port), DashboardHandler)
    print(f"\n⚡ Live Dashboard running at: http://localhost:{port}")
    print(f"   Watching: {args.services_dir} for '{args.feature}' scenarios")
    print("   Press Ctrl+C to stop.\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping dashboard server.")
        server.server_close()


def run_watch(args, out_path):
    """Run file watcher loop to regenerate static HTML on disk when files change."""
    import time

    def regenerate():
        scenarios = scan_feature_scenarios(args.services_dir, args.feature)
        if not scenarios:
            return
        html_out = render_feature_dashboard(scenarios, args.feature, title=args.title)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(html_out, encoding="utf-8")
        print(f"[watch] Regenerated dashboard ({len(scenarios)} scenarios) -> {out_path} at {time.strftime('%H:%M:%S')}")

    regenerate()
    last_fp = get_scenarios_fingerprint(args.services_dir)
    print(f"\n👀 Watching {args.services_dir} for '{args.feature}' changes (Ctrl+C to stop)...")
    try:
        while True:
            time.sleep(1.0)
            curr_fp = get_scenarios_fingerprint(args.services_dir)
            if curr_fp > last_fp:
                last_fp = curr_fp
                regenerate()
    except KeyboardInterrupt:
        print("\nStopping watcher.")


def main():
    default_services = find_default_services_dir()
    parser = argparse.ArgumentParser(
        description="Generate cross-service feature dashboard for trust-me-bro-ai."
    )
    parser.add_argument(
        "--services-dir",
        default=str(default_services),
        help=f"Root directory containing microservices (default auto-detected: {default_services})",
    )
    parser.add_argument(
        "--feature",
        "-f",
        default="BIZ_AI",
        help="Feature keyword to scan (e.g. BIZ_AI, BROADCAST, or ALL)",
    )
    parser.add_argument(
        "--output",
        "-o",
        default=None,
        help="Output HTML dashboard file path (default: feature-<slug>-dashboard.html)",
    )
    parser.add_argument(
        "--title",
        default=None,
        help="Custom dashboard title (default: auto-generated from feature name)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify the generated dashboard HTML without writing",
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Watch work/Scenario/ across services and regenerate output on disk on changes",
    )
    parser.add_argument(
        "--serve",
        nargs="?",
        const=8080,
        type=int,
        help="Serve dashboard with zero-dependency auto-reloading dev server (default port: 8080)",
    )

    args = parser.parse_args()

    # Derive default output path
    if args.output:
        out_path = Path(args.output).resolve()
    else:
        slug = args.feature.lower().replace("_", "-")
        base_dir = Path(args.services_dir).parent if Path(args.services_dir).name == "services" else Path.cwd()
        filename = "feature-biz-ai-integration.html" if slug == "biz-ai" else f"feature-{slug}-dashboard.html"
        out_path = (base_dir / filename).resolve()

    if args.serve:
        run_serve(args, out_path, port=args.serve)
        return

    if args.watch:
        run_watch(args, out_path)
        return

    scenarios = scan_feature_scenarios(args.services_dir, args.feature)
    if not scenarios:
        print(f"No scenarios found for feature: {args.feature} in {args.services_dir}")
        sys.exit(1)

    print(
        f"Found {len(scenarios)} scenarios across {len(set(s['service'] for s in scenarios))} services for feature '{args.feature}'."
    )
    for sc in scenarios:
        print(
            f"  [{sc['service']}] {sc['category']} / {sc['scenario']} ({sc['stages_done']}/6 stages, {sc['total_tasks']} tasks)"
        )

    html_out = render_feature_dashboard(
        scenarios, args.feature, title=args.title
    )

    is_valid, errors, unclosed = verify_balanced_tags(html_out)
    if not is_valid:
        print("HTML validation errors:")
        for err in errors:
            print(" ", err)
        for tag, pos in unclosed:
            print(f"  unclosed <{tag}> opened at {pos}")
        sys.exit(1)

    if args.check:
        print("[ok] Dashboard HTML passed structural validation.")
        return

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html_out, encoding="utf-8")
    print(f"[ok] Dashboard successfully written to: {out_path}")


if __name__ == "__main__":
    main()
