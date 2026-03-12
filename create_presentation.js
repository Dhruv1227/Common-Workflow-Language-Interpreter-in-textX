const pptxgen = require('pptxgenjs');
const {
  imageSizingContain,
  calcTextBox,
  warnIfSlideHasOverlaps,
  warnIfSlideElementsOutOfBounds,
  safeOuterShadow,
} = require('/home/oai/skills/slides/pptxgenjs_helpers');
const fs = require('fs');
const path = require('path');

const pptx = new pptxgen();
pptx.layout = 'LAYOUT_WIDE';
pptx.author = 'OpenAI';
pptx.company = 'OpenAI';
pptx.subject = 'LeadFlowML DSL';
pptx.title = 'LeadFlowML DSL – Sales Lead Classification';
pptx.lang = 'en-US';
tpptx = pptx;
pptx.theme = {
  headFontFace: 'Aptos Display',
  bodyFontFace: 'Aptos',
  lang: 'en-US'
};
pptx.defineSlideMaster({
  title: 'MASTER',
  background: { color: 'F7F9FC' },
  objects: [
    { rect: { x: 0, y: 0, w: 13.333, h: 0.18, fill: { color: '17324D' }, line: { color: '17324D' } } },
    { text: { text: 'LeadFlowML DSL', options: { x: 0.5, y: 7.08, w: 2.2, h: 0.2, fontSize: 8, color: '6B7785' } } }
  ],
  slideNumber: { x: 12.6, y: 7.02, w: 0.35, h: 0.2, fontSize: 8, color: '6B7785', align: 'right' }
});

const ROOT = '/mnt/data/LeadFlowML_Project';
const metricsImg = path.join(ROOT, 'artifacts', 'metrics_comparison.png');
const histImg = path.join(ROOT, 'artifacts', 'prediction_distribution.png');
const outPath = path.join(ROOT, 'LeadFlowML_Presentation.pptx');
const report = JSON.parse(fs.readFileSync(path.join(ROOT, 'outputs', 'evaluation_report.json'), 'utf8'));
const reportRF = JSON.parse(fs.readFileSync(path.join(ROOT, 'outputs', 'evaluation_report_rf.json'), 'utf8'));
const workflowSnippet = fs.readFileSync(path.join(ROOT, 'generated_cwl', 'workflow.cwl'), 'utf8').split('\n').slice(0, 22).join('\n');
const dslSnippet = fs.readFileSync(path.join(ROOT, 'workflows', 'lead_qualification.leadflow'), 'utf8').split('\n').slice(0, 18).join('\n');

function addTitle(slide, title, subtitle) {
  slide.addText(title, { x: 0.55, y: 0.45, w: 6.9, h: 0.45, fontSize: 26, bold: true, color: '17324D' });
  if (subtitle) slide.addText(subtitle, { x: 0.56, y: 0.95, w: 8.5, h: 0.32, fontSize: 12, color: '5A6B7D' });
}
function addPill(slide, text, x, y, w) {
  slide.addShape(pptx.ShapeType.roundRect, { x, y, w, h: 0.34, rectRadius: 0.08, fill: { color: 'E9F1FF' }, line: { color: 'C7D8F6' } });
  slide.addText(text, { x: x + 0.06, y: y + 0.06, w: w - 0.12, h: 0.18, fontSize: 10, color: '17324D', align: 'center', bold: true });
}
function addSourceNotes(slide, lines) {
  slide.addNotes(`[Sources]\n${lines.map(s => '- ' + s).join('\n')}`);
}

// Slide 1
{
  const slide = pptx.addSlide('MASTER');
  slide.addText('LeadFlowML DSL', { x: 0.72, y: 1.05, w: 5.3, h: 0.7, fontSize: 28, bold: true, color: '17324D' });
  slide.addText('A textX + CWL approach for classifying new sales cases from historical training data', { x: 0.74, y: 1.86, w: 8.4, h: 0.5, fontSize: 18, color: '4C6276' });
  addPill(slide, 'textX grammar', 0.78, 2.7, 1.65);
  addPill(slide, 'CWL generation', 2.58, 2.7, 1.8);
  addPill(slide, 'ML scoring', 4.54, 2.7, 1.55);
  addPill(slide, 'Jupyter demo', 6.25, 2.7, 1.7);
  // central workflow strip
  slide.addShape(pptx.ShapeType.line, { x: 1.25, y: 4.15, w: 10.2, h: 0, line: { color: 'B9C7D6', width: 2 } });
  const xs = [1.0, 3.55, 6.1, 8.65, 11.0];
  const labels = [
    ['sales', 'data'],
    ['DSL', 'spec'],
    ['generated', 'CWL'],
    ['trained', 'model'],
    ['new-case', 'predictions']
  ];
  xs.forEach((x, i) => {
    slide.addShape(pptx.ShapeType.ellipse, { x, y: 3.6, w: 0.88, h: 0.88, fill: { color: i % 2 === 0 ? '17324D' : '2C7DA0' }, line: { color: 'FFFFFF', width: 1.5 } });
    slide.addText(labels[i][0], { x: x-0.05, y: 4.75, w: 1.0, h: 0.2, fontSize: 11, align: 'center', bold: true, color: '17324D' });
    slide.addText(labels[i][1], { x: x-0.05, y: 4.96, w: 1.0, h: 0.2, fontSize: 11, align: 'center', color: '17324D' });
  });
  slide.addText('End-to-end project package: executive summary, executed notebook, source package, and presentation', { x: 0.78, y: 6.15, w: 9.0, h: 0.35, fontSize: 16, color: '17324D' });
  warnIfSlideHasOverlaps(slide, pptx);
  warnIfSlideElementsOutOfBounds(slide, pptx);
}

// Slide 2
{
  const slide = pptx.addSlide('MASTER');
  addTitle(slide, 'Why use a DSL here?', 'The project translates domain intent into a reproducible workflow.');

  // arrows first
  slide.addShape(pptx.ShapeType.line, { x: 3.55, y: 3.1, w: 1.0, h: 0, line: { color: '7AA7D9', width: 2.2, endArrowType: 'triangle' } });
  slide.addShape(pptx.ShapeType.line, { x: 7.98, y: 3.1, w: 1.0, h: 0, line: { color: '7AA7D9', width: 2.2, endArrowType: 'triangle' } });

  const cards = [
    { x: 0.7, title: 'Domain abstraction', body: 'The analyst writes business concepts like data, features, model, metrics, and outputs instead of low-level orchestration code.' },
    { x: 4.45, title: 'Portable workflow', body: 'The DSL is compiled into reusable CWL CommandLineTools and a Workflow with explicit inputs, outputs, and dependencies.' },
    { x: 8.85, title: 'Execution clarity', body: 'Training, validation, and scoring remain separate tools, so results are easier to test, reproduce, and explain.' },
  ];
  cards.forEach(c => {
    slide.addShape(pptx.ShapeType.roundRect, { x: c.x, y: 2.0, w: 3.15, h: 2.25, rectRadius: 0.08, fill: { color: 'FFFFFF' }, line: { color: 'D5DFEA', width: 1.2 }, shadow: safeOuterShadow('000000', 0.12, 45, 1.5, 0.5) });
    slide.addText(c.title, { x: c.x + 0.2, y: 2.2, w: 2.7, h: 0.35, fontSize: 18, bold: true, color: '17324D' });
    slide.addText(c.body, { x: c.x + 0.2, y: 2.75, w: 2.75, h: 1.2, fontSize: 13, color: '4B5E70', valign: 'mid' });
  });
  slide.addText('Key design choice: keep the user-facing language compact, then let the processor generate the executable workflow layer.', { x: 0.84, y: 5.15, w: 10.8, h: 0.45, fontSize: 17, color: '17324D' });
  addPill(slide, 'grammar → model', 0.85, 5.95, 2.1);
  addPill(slide, 'CommandLineTool + Workflow', 3.2, 5.95, 3.0);
  addPill(slide, 'reusable ML components', 6.48, 5.95, 2.7);
  addSourceNotes(slide, [
    'Tomassetti, Quick Domain-Specific Languages in Python with textX (textX uses the same meta-language to define grammar and model structure).',
    'Karle et al., Parsl+CWL: Towards Combining the Python and CWL Ecosystems (CWL CommandLineTools and Workflows, portability, and runner responsibilities).'
  ]);
  warnIfSlideHasOverlaps(slide, pptx);
  warnIfSlideElementsOutOfBounds(slide, pptx);
}

// Slide 3
{
  const slide = pptx.addSlide('MASTER');
  addTitle(slide, 'DSL surface syntax', 'One compact specification is enough to describe the ML case-classification pipeline.');
  slide.addShape(pptx.ShapeType.roundRect, { x: 0.7, y: 1.6, w: 6.2, h: 5.25, rectRadius: 0.06, fill: { color: '13253A' }, line: { color: '13253A' } });
  slide.addText(dslSnippet, { x: 0.95, y: 1.92, w: 5.65, h: 4.8, fontFace: 'Consolas', fontSize: 13, color: 'F5F7FA', margin: 0.04 });

  slide.addShape(pptx.ShapeType.roundRect, { x: 7.3, y: 1.75, w: 5.35, h: 1.18, rectRadius: 0.05, fill: { color: 'E8F0FE' }, line: { color: 'BFD1F0' } });
  slide.addText('Semantic mapping', { x: 7.6, y: 1.95, w: 2.5, h: 0.25, fontSize: 18, bold: true, color: '17324D' });
  slide.addText('• data → workflow inputs\n• features → preprocessing schema\n• model → training/evaluation behavior\n• outputs → artifact locations', { x: 7.6, y: 2.28, w: 4.5, h: 0.55, fontSize: 13, color: '4B5E70' });

  const sem = [
    'Target users edit file paths, feature groups, algorithm choice, and classification threshold without touching Python internals.',
    'The same grammar supports multiple scenarios: default logistic regression and an alternate random-forest version are both included in the package.',
    'This keeps the language focused on the business problem rather than general-purpose syntax.'
  ];
  let y = 3.25;
  sem.forEach((txt, i) => {
    slide.addShape(pptx.ShapeType.ellipse, { x: 7.42, y: y + 0.02, w: 0.16, h: 0.16, fill: { color: '2C7DA0' }, line: { color: '2C7DA0' } });
    slide.addText(txt, { x: 7.7, y, w: 4.5, h: 0.58, fontSize: 14, color: '17324D' });
    y += 0.92;
  });

  addPill(slide, 'default scenario', 7.55, 6.15, 1.6);
  addPill(slide, 'alternate scenario', 9.35, 6.15, 1.8);
  warnIfSlideHasOverlaps(slide, pptx);
  warnIfSlideElementsOutOfBounds(slide, pptx);
}

// Slide 4
{
  const slide = pptx.addSlide('MASTER');
  addTitle(slide, 'Implementation architecture', 'textX parsing and CWL generation separate language design from execution mechanics.');
  // connectors first
  const cx = [1.0, 3.35, 5.8, 8.3, 10.7];
  for (let i = 0; i < cx.length - 1; i++) {
    slide.addShape(pptx.ShapeType.line, { x: cx[i] + 1.2, y: 3.35, w: 1.0, h: 0, line: { color: '7AA7D9', width: 2, endArrowType: 'triangle' } });
  }
  const boxes = [
    ['LeadFlow DSL', 'Human-authored spec'],
    ['textX model', 'Parsed object graph'],
    ['DSL processor', 'Generates CWL + JSON'],
    ['ML runtime', 'validate/train/score'],
    ['Artifacts', 'model + report + CSV']
  ];
  boxes.forEach((b, i) => {
    slide.addShape(pptx.ShapeType.roundRect, { x: cx[i], y: 2.55, w: 1.9, h: 1.5, rectRadius: 0.06, fill: { color: i % 2 === 0 ? 'FFFFFF' : 'EEF5FF' }, line: { color: 'C7D8EA', width: 1.2 } });
    slide.addText(b[0], { x: cx[i] + 0.15, y: 2.85, w: 1.6, h: 0.28, fontSize: 16, bold: true, align: 'center', color: '17324D' });
    slide.addText(b[1], { x: cx[i] + 0.15, y: 3.25, w: 1.6, h: 0.42, fontSize: 11.5, align: 'center', color: '4B5E70' });
  });
  slide.addText('Reusable CWL steps', { x: 0.95, y: 5.05, w: 2.2, h: 0.25, fontSize: 16, bold: true, color: '17324D' });
  ['validate_data.cwl', 'train_model.cwl', 'score_cases.cwl', 'workflow.cwl'].forEach((f, idx) => {
    slide.addShape(pptx.ShapeType.roundRect, { x: 1.0 + idx * 1.9, y: 5.45, w: 1.55, h: 0.58, rectRadius: 0.03, fill: { color: '17324D' }, line: { color: '17324D' } });
    slide.addText(f, { x: 1.05 + idx * 1.9, y: 5.64, w: 1.45, h: 0.15, fontFace: 'Consolas', fontSize: 9.6, color: 'FFFFFF', align: 'center' });
  });
  slide.addText('The architecture follows the literature emphasis on reusable components, explicit tool interfaces, and portable workflow descriptions.', { x: 8.5, y: 5.0, w: 4.0, h: 0.8, fontSize: 15, color: '17324D' });
  addSourceNotes(slide, [
    'Karle et al., Parsl+CWL (CWL tool definitions become reusable executable components; workflows specify dependencies rather than execution order).',
    'Lampa et al., SciPipe (reusable components, parameterized ML workflows, and reduced fragmentation are important for complex ML pipelines).'
  ]);
  warnIfSlideHasOverlaps(slide, pptx);
  warnIfSlideElementsOutOfBounds(slide, pptx);
}

// Slide 5
{
  const slide = pptx.addSlide('MASTER');
  addTitle(slide, 'Generated CWL workflow', 'The DSL processor emits standard CWL YAML rather than a custom runtime-only format.');
  slide.addShape(pptx.ShapeType.roundRect, { x: 0.72, y: 1.65, w: 6.1, h: 5.0, rectRadius: 0.05, fill: { color: 'FFFFFF' }, line: { color: 'D7E1EC', width: 1.2 } });
  slide.addText(workflowSnippet, { x: 0.95, y: 1.95, w: 5.6, h: 4.5, fontFace: 'Consolas', fontSize: 12, color: '17324D', margin: 0.02 });

  // workflow diagram on right, connectors first
  slide.addShape(pptx.ShapeType.line, { x: 8.55, y: 2.6, w: 0, h: 0.72, line: { color: '7AA7D9', width: 2, endArrowType: 'triangle' } });
  slide.addShape(pptx.ShapeType.line, { x: 10.7, y: 3.45, w: 0, h: 0.72, line: { color: '7AA7D9', width: 2, endArrowType: 'triangle' } });
  slide.addShape(pptx.ShapeType.line, { x: 12.55, y: 3.45, w: -1.05, h: 0, line: { color: '7AA7D9', width: 2, endArrowType: 'triangle' } });

  slide.addShape(pptx.ShapeType.roundRect, { x: 7.6, y: 1.8, w: 1.9, h: 0.7, rectRadius: 0.05, fill: { color: 'E8F0FE' }, line: { color: 'BFD1F0' } });
  slide.addText('validate', { x: 7.9, y: 2.03, w: 1.3, h: 0.18, fontSize: 18, bold: true, align: 'center', color: '17324D' });
  slide.addShape(pptx.ShapeType.roundRect, { x: 9.7, y: 3.0, w: 1.95, h: 0.7, rectRadius: 0.05, fill: { color: '17324D' }, line: { color: '17324D' } });
  slide.addText('train', { x: 10.02, y: 3.24, w: 1.3, h: 0.18, fontSize: 18, bold: true, align: 'center', color: 'FFFFFF' });
  slide.addShape(pptx.ShapeType.roundRect, { x: 10.95, y: 4.25, w: 1.95, h: 0.7, rectRadius: 0.05, fill: { color: '2C7DA0' }, line: { color: '2C7DA0' } });
  slide.addText('score', { x: 11.25, y: 4.49, w: 1.3, h: 0.18, fontSize: 18, bold: true, align: 'center', color: 'FFFFFF' });
  slide.addText('Outputs', { x: 7.65, y: 5.45, w: 1.5, h: 0.2, fontSize: 16, bold: true, color: '17324D' });
  const outs = ['validation_report.json', 'evaluation_report.json', 'new_case_predictions.csv'];
  outs.forEach((o, idx) => {
    slide.addShape(pptx.ShapeType.roundRect, { x: 7.65, y: 5.8 + idx * 0.34, w: 3.65, h: 0.28, rectRadius: 0.03, fill: { color: idx === 1 ? '17324D' : 'EEF5FF' }, line: { color: 'BFD1F0' } });
    slide.addText(o, { x: 7.82, y: 5.87 + idx * 0.34, w: 3.15, h: 0.12, fontFace: 'Consolas', fontSize: 9.5, color: idx === 1 ? 'FFFFFF' : '17324D' });
  });
  addSourceNotes(slide, [
    'Karle et al., Parsl+CWL (CommandLineTools define interfaces; Workflows connect steps via inputs/outputs; cwltool validates and executes CWL descriptions).'
  ]);
  warnIfSlideHasOverlaps(slide, pptx);
  warnIfSlideElementsOutOfBounds(slide, pptx);
}

// Slide 6
{
  const slide = pptx.addSlide('MASTER');
  addTitle(slide, 'Notebook demo results', 'Two scenarios were executed from the same DSL family: default logistic regression and alternate random forest.');
  slide.addImage({ path: metricsImg, ...imageSizingContain(metricsImg, 0.65, 1.55, 7.0, 4.15) });
  slide.addImage({ path: histImg, ...imageSizingContain(histImg, 8.0, 1.55, 4.8, 3.25) });
  slide.addShape(pptx.ShapeType.roundRect, { x: 8.15, y: 5.1, w: 4.45, h: 1.35, rectRadius: 0.05, fill: { color: 'FFFFFF' }, line: { color: 'D7E1EC', width: 1.2 } });
  slide.addText(`Default model\nAccuracy ${report.metrics.accuracy.toFixed(3)}   F1 ${report.metrics.f1.toFixed(3)}\nCV mean F1 ${report.metrics.cv_f1_mean.toFixed(3)}\n\nAlt model\nAccuracy ${reportRF.metrics.accuracy.toFixed(3)}   F1 ${reportRF.metrics.f1.toFixed(3)}`, {
    x: 8.4, y: 5.35, w: 3.8, h: 0.9, fontSize: 14, color: '17324D', margin: 0.02
  });
  slide.addText('Takeaway: the notebook demonstrates that changing the DSL specification changes the end-to-end behavior without changing the orchestration code.', { x: 0.78, y: 6.35, w: 7.2, h: 0.3, fontSize: 15, color: '17324D' });
  warnIfSlideHasOverlaps(slide, pptx);
  warnIfSlideElementsOutOfBounds(slide, pptx);
}

// Slide 7
{
  const slide = pptx.addSlide('MASTER');
  addTitle(slide, 'Submission package', 'Everything requested in the assignment is included as a coherent project package.');
  slide.addShape(pptx.ShapeType.roundRect, { x: 0.8, y: 1.8, w: 5.6, h: 4.9, rectRadius: 0.05, fill: { color: '13253A' }, line: { color: '13253A' } });
  const tree = [
    'LeadFlowML_Project/',
    '├── Executive_Summary_LeadFlowML.docx',
    '├── notebooks/LeadFlowML_demo_executed.ipynb',
    '├── dsl/leadflow.tx',
    '├── workflows/*.leadflow',
    '├── src/*.py',
    '├── generated_cwl/*.cwl',
    '├── data/*.csv',
    '├── outputs/*.json, *.csv',
    '└── README.md'
  ].join('\n');
  slide.addText(tree, { x: 1.05, y: 2.2, w: 5.0, h: 4.1, fontFace: 'Consolas', fontSize: 14, color: 'F5F7FA', margin: 0.02 });

  const checks = [
    'Executive summary in Word',
    'Executed notebook showing multiple scenarios',
    'Full source package ready to zip and upload',
    'Presentation deck for the group contest'
  ];
  slide.addText('Checklist', { x: 7.25, y: 2.0, w: 2.0, h: 0.25, fontSize: 20, bold: true, color: '17324D' });
  let y = 2.55;
  checks.forEach(txt => {
    slide.addShape(pptx.ShapeType.ellipse, { x: 7.28, y: y + 0.04, w: 0.16, h: 0.16, fill: { color: '2C7DA0' }, line: { color: '2C7DA0' } });
    slide.addText(txt, { x: 7.58, y, w: 4.5, h: 0.3, fontSize: 16, color: '17324D' });
    y += 0.78;
  });
  slide.addShape(pptx.ShapeType.roundRect, { x: 7.25, y: 5.7, w: 4.85, h: 0.8, rectRadius: 0.05, fill: { color: 'E8F0FE' }, line: { color: 'BFD1F0' } });
  slide.addText('Recommended upload: one ZIP containing the project folder plus the PPTX copy if D2L asks for separate files.', { x: 7.5, y: 5.92, w: 4.4, h: 0.36, fontSize: 14, color: '17324D' });
  warnIfSlideHasOverlaps(slide, pptx);
  warnIfSlideElementsOutOfBounds(slide, pptx);
}

// Slide 8
{
  const slide = pptx.addSlide('MASTER');
  slide.addText('End-to-end DSL lifecycle', { x: 0.9, y: 1.55, w: 6.4, h: 0.38, fontSize: 26, bold: true, color: '17324D' });
  slide.addText('Design a domain language → parse with textX → generate CWL → run ML workflow → classify new cases', { x: 0.92, y: 2.12, w: 11.0, h: 0.32, fontSize: 17, color: '4C6276' });
  addPill(slide, 'domain clarity', 1.0, 3.25, 1.7);
  addPill(slide, 'portable execution', 2.95, 3.25, 2.0);
  addPill(slide, 'reproducible outputs', 5.25, 3.25, 2.1);
  addPill(slide, 'easy scenario switching', 7.65, 3.25, 2.2);
  slide.addShape(pptx.ShapeType.roundRect, { x: 1.15, y: 4.2, w: 11.0, h: 1.4, rectRadius: 0.08, fill: { color: '17324D' }, line: { color: '17324D' } });
  slide.addText('Next extension ideas: hyperparameter sweeps, model registry export, deployment targets, or richer validation rules in the DSL.', { x: 1.45, y: 4.68, w: 10.3, h: 0.38, fontSize: 18, color: 'FFFFFF', align: 'center' });
  warnIfSlideHasOverlaps(slide, pptx);
  warnIfSlideElementsOutOfBounds(slide, pptx);
}

pptx.writeFile({ fileName: outPath });
