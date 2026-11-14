<!doctype html>
<html lang="en" data-base="{{base_path}}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <meta name="theme-color" content="#0b1329">
  <meta name="description" content="StoryFlow AI local knowledge and content intake workspace.">
  <title>StoryFlow AI · Knowledge Intake</title>
  <link rel="stylesheet" href="{{base_path}}/assets/styles.css">
  <script defer src="{{base_path}}/assets/main.js"></script>
</head>
<body>
  <div class="layout">
    <aside class="sidebar" aria-label="Workspace navigation">
      <div class="brand"><div class="brand-mark">S<span>✦</span></div><div><b>StoryFlow <em>AI</em></b><small>Intelligence workspace</small></div></div>
      <div class="nav-label">WORKSPACE</div>
      <nav class="sidebar-nav">
        <a href="{{base_path}}/" aria-current="page"><span class="nav-icon">▦</span> Knowledge intake <span class="active-dot"></span></a>
        <div class="disabled-nav"><span class="nav-icon">◫</span> Content review <span class="soon">Next</span></div>
        <div class="disabled-nav"><span class="nav-icon">▤</span> Goal planning <span class="soon">Next</span></div>
        <div class="disabled-nav"><span class="nav-icon">▦</span> Schedule <span class="soon">Next</span></div>
      </nav>
      <div class="sidebar-foot"><div class="status-dot"></div><div><strong>Local workspace</strong><small>No account required · No cloud sync</small></div></div>
    </aside>

    <div class="main-wrap">
      <header class="topbar"><span>Workspace <span class="chevron">/</span> <b>Knowledge intake</b></span><div class="topbar-actions"><span class="pill"><span class="tiny-dot"></span> Internal demo</span><span class="avatar" aria-label="Local operator">IO</span></div></header>
      <main class="main-content">
        <div class="eyebrow">FOUNDATION · STEP 01 OF 04</div>
        <section class="hero">
          <div class="hero-copy"><span class="hero-badge">✦ &nbsp; Ground your AI workspace</span><h1>Every great workflow<br>starts with a <span>clear purpose.</span></h1><p>Give StoryFlow the knowledge that defines your platform, or stage a content campaign. Review stays in human hands. Nothing is published or sent from this workspace.</p><div class="hero-tags"><span>✓ Local JSON</span><span>✓ Zero account setup</span><span>✓ Human-first</span></div></div>
          <div class="hero-art" aria-hidden="true"><div class="orbit outer"></div><div class="orbit inner"></div><div class="core">✦</div><span class="spark a">✧</span><span class="spark b">✦</span><span class="spark c">✶</span></div>
        </section>

        <section class="summary-grid" aria-label="Workspace status">
          <div class="metric"><span class="metric-icon lavender">✧</span><div><span class="metric-label">Knowledge source</span><strong id="metric-knowledge">Not loaded</strong></div></div>
          <div class="metric"><span class="metric-icon teal">⇧</span><div><span class="metric-label">Staged datasets</span><strong id="metric-datasets">0</strong></div></div>
          <div class="metric"><span class="metric-icon blue">◈</span><div><span class="metric-label">AI drafts to review</span><strong id="metric-drafts">0</strong></div></div>
        </section>

        <div class="section-heading"><div><span class="eyebrow">GET STARTED</span><h2>Bring your knowledge into focus</h2><p>Upload a JSON file to establish your platform's goal or stage your campaign data.</p></div><a class="quiet-link" href="{{base_path}}/examples/knowledge.json" download="knowledge.example.json">↓ Download example knowledge</a></div>

        <div class="cards-grid">
          <section class="surface upload-panel" aria-labelledby="upload-title">
            <div class="card-top"><div class="card-icon">⇧</div><span class="step-tag">01 · UPLOAD</span></div>
            <h3 id="upload-title">Import a knowledge file</h3><p class="card-desc">Accepts the StoryFlow <code>platform_knowledge</code> format or your existing campaign datasets.</p>
            <form id="import-form" enctype="multipart/form-data">
              <div class="dropzone" id="dropzone" tabindex="0" role="button" aria-label="Choose a JSON file to upload">
                <span class="upload-glyph">⇧</span><strong id="drop-title">Drop a JSON file here</strong><span id="drop-caption">or click to browse from your computer</span><span class="file-restriction">.JSON only · Up to 2 MB</span>
              </div>
              <input id="file-input" name="file" type="file" accept=".json,application/json" required hidden>
              <button type="submit" class="primary-button" id="import-button" disabled>Stage JSON file <span aria-hidden="true">→</span></button>
            </form>
            <p id="import-message" class="feedback" role="status" aria-live="polite"></p>
          </section>

          <section class="surface knowledge-panel" aria-labelledby="knowledge-title">
            <div class="card-top"><div class="card-icon green">◎</div><span class="step-tag">02 · UNDERSTAND</span></div>
            <h3 id="knowledge-title">Platform knowledge</h3><p class="card-desc">Your latest uploaded knowledge file establishes the purpose and guardrails for future processing.</p>
            <div id="knowledge-empty" class="empty-state"><div class="empty-icon">◇</div><strong>No platform knowledge yet</strong><p>Start with the example file or define your own platform goal.</p></div>
            <div id="knowledge-loaded" hidden><span class="field-label">PLATFORM</span><h4 id="knowledge-name"></h4><span class="field-label">PRIMARY GOAL</span><p class="goal-text" id="knowledge-goal"></p><span class="field-label">AUDIENCES</span><div class="tags" id="knowledge-audiences"></div><div class="small-foot" id="knowledge-filename"></div></div>
          </section>
        </div>

        <section class="surface dataset-panel" aria-labelledby="datasets-title"><div class="row-head"><div><span class="eyebrow">STAGED INPUTS</span><h2 id="datasets-title">Your content datasets</h2><p>Imports are preserved locally and await a future human review workflow.</p></div><span class="neutral-pill" id="dataset-count">0 imported</span></div><div id="dataset-empty" class="dataset-empty">No campaign data uploaded yet. Try the 30-day ProgramLift sample JSON from your project materials.</div><div id="dataset-list" class="dataset-list" aria-live="polite"></div></section>

        <section class="next-section"><div><span class="eyebrow">WHAT COMES NEXT</span><h2>One foundation. A complete workflow.</h2></div><div class="process-grid"><div class="process-step now"><span>01</span><strong>Import</strong><small>Knowledge + data</small></div><div class="process-step"><span>02</span><strong>Analyze</strong><small>AI draft inspection</small></div><div class="process-step"><span>03</span><strong>Verify</strong><small>Human decisions</small></div><div class="process-step"><span>04</span><strong>Plan & schedule</strong><small>Approved content only</small></div></div></section>
        <p class="safety-note">◈ &nbsp; Local-only development starter. There is no authentication. Keep the server bound to <code>127.0.0.1</code> and don't upload private participant or client information to an unprotected workspace.</p>
      </main>
    </div>
  </div>
</body>
</html>
