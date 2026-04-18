<script setup>
import { computed, ref } from "vue";

const page = ref("home");
const resumeText = ref("");
const jobDescription = ref("");
const analysis = ref(null);
const optimized = ref(null);
const loadingAnalysis = ref(false);
const loadingOptimization = ref(false);
const uploadLoading = ref(false);
const errorMessage = ref("");
const uploadedFilename = ref("");

const steps = [
  { key: "resume", number: "01", title: "输入简历" },
  { key: "jd", number: "02", title: "输入目标职位" },
  { key: "analysis", number: "03", title: "查看匹配分析" },
  { key: "result", number: "04", title: "查看优化成品" },
];

const canContinueResume = computed(() => resumeText.value.trim().length >= 20);
const canAnalyze = computed(() => canContinueResume.value && jobDescription.value.trim().length >= 20);
const renderedResumeHtml = computed(() =>
  optimized.value ? markdownToResumeHtml(optimized.value.optimized_resume_markdown) : "",
);

const currentStepIndex = computed(() => {
  switch (page.value) {
    case "home":
      return -1;
    case "resume":
      return 0;
    case "jd":
      return 1;
    case "analyzing":
    case "analysis":
      return 2;
    case "optimizing":
    case "result":
      return 3;
    default:
      return 0;
  }
});

const waitingTitle = computed(() => {
  if (page.value === "analyzing") return "正在分析简历与岗位匹配度";
  if (page.value === "optimizing") return "正在生成优化后的简历成品";
  return "";
});

const waitingDescription = computed(() => {
  if (page.value === "analyzing") {
    return "系统正在提取岗位关键词、识别亮点与缺口，并整理针对性的修改建议。";
  }
  if (page.value === "optimizing") {
    return "系统正在根据分析结果重写简历结构与表述，输出可直接查看和导出的中文简历成品。";
  }
  return "";
});

function resetResults() {
  analysis.value = null;
  optimized.value = null;
  errorMessage.value = "";
}

function startFlow() {
  errorMessage.value = "";
  page.value = "resume";
}

function goToStep(target) {
  errorMessage.value = "";

  if (target === "resume") {
    page.value = "resume";
    return;
  }

  if (target === "jd" && canContinueResume.value) {
    page.value = "jd";
    return;
  }

  if (target === "analysis" && analysis.value) {
    page.value = "analysis";
    return;
  }

  if (target === "result" && optimized.value) {
    page.value = "result";
  }
}

async function handleFileUpload(event) {
  const [file] = event.target.files || [];
  if (!file) return;

  uploadLoading.value = true;
  errorMessage.value = "";
  optimized.value = null;

  try {
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch("/api/v1/parse-resume", {
      method: "POST",
      body: formData,
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "简历文件解析失败。");
    }

    resumeText.value = data.resume_text;
    uploadedFilename.value = data.filename;
    resetResults();
  } catch (error) {
    errorMessage.value = error.message;
  } finally {
    uploadLoading.value = false;
    event.target.value = "";
  }
}

async function analyzeMatch() {
  if (!canAnalyze.value) return;

  loadingAnalysis.value = true;
  errorMessage.value = "";
  optimized.value = null;
  page.value = "analyzing";

  try {
    const response = await fetch("/api/v1/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        resume_text: resumeText.value,
        job_description: jobDescription.value,
      }),
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "简历匹配分析失败。");
    }

    analysis.value = data;
    page.value = "analysis";
  } catch (error) {
    errorMessage.value = error.message;
    page.value = "jd";
  } finally {
    loadingAnalysis.value = false;
  }
}

async function generateOptimizedResume() {
  if (!analysis.value) return;

  loadingOptimization.value = true;
  errorMessage.value = "";
  page.value = "optimizing";

  try {
    const response = await fetch("/api/v1/optimize", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        resume_text: resumeText.value,
        job_description: jobDescription.value,
        analysis_context: analysis.value,
      }),
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "优化简历生成失败。");
    }

    optimized.value = data;
    page.value = "result";
  } catch (error) {
    errorMessage.value = error.message;
    page.value = "analysis";
  } finally {
    loadingOptimization.value = false;
  }
}

function restartFlow() {
  page.value = "home";
  resumeText.value = "";
  jobDescription.value = "";
  analysis.value = null;
  optimized.value = null;
  errorMessage.value = "";
  uploadedFilename.value = "";
}

function downloadText(filename, content) {
  const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  document.body.removeChild(anchor);
  URL.revokeObjectURL(url);
}

function exportMarkdown() {
  if (!optimized.value) return;
  downloadText("优化后简历.md", optimized.value.optimized_resume_markdown);
}

function exportTxt() {
  if (!optimized.value) return;
  downloadText("优化后简历.txt", optimized.value.optimized_resume_markdown);
}

function escapeHtml(value) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function formatInlineMarkdown(value) {
  return escapeHtml(value)
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.+?)\*/g, "<em>$1</em>");
}

function markdownToResumeHtml(markdown) {
  const lines = markdown.split("\n");
  const html = [];
  let listBuffer = [];

  const flushList = () => {
    if (!listBuffer.length) return;
    html.push(`<ul>${listBuffer.join("")}</ul>`);
    listBuffer = [];
  };

  for (const rawLine of lines) {
    const line = rawLine.trim();

    if (!line) {
      flushList();
      continue;
    }

    if (line.startsWith("- ") || line.startsWith("* ")) {
      listBuffer.push(`<li>${formatInlineMarkdown(line.slice(2).trim())}</li>`);
      continue;
    }

    flushList();

    if (line.startsWith("### ")) {
      html.push(`<h3>${formatInlineMarkdown(line.slice(4).trim())}</h3>`);
      continue;
    }
    if (line.startsWith("## ")) {
      html.push(`<h2>${formatInlineMarkdown(line.slice(3).trim())}</h2>`);
      continue;
    }
    if (line.startsWith("# ")) {
      html.push(`<h1>${formatInlineMarkdown(line.slice(2).trim())}</h1>`);
      continue;
    }

    html.push(`<p>${formatInlineMarkdown(line)}</p>`);
  }

  flushList();
  return html.join("");
}
</script>

<template>
  <div class="app-shell">
    <div class="bg-orb orb-a"></div>
    <div class="bg-orb orb-b"></div>

    <template v-if="page === 'home'">
      <main class="landing">
        <section class="landing-hero card">
          <p class="eyebrow">简历优化 Agent</p>
          <h1>一站式完成简历分析、优化与成品导出</h1>
          <p class="lead">
            针对目标岗位描述，先给出匹配亮点、核心缺口和修改建议，再生成一份可直接查看与导出的中文简历成品。
          </p>

          <div class="landing-actions">
            <button class="primary-button large" @click="startFlow">进入简历优化</button>
          </div>

          <div class="feature-grid">
            <article class="feature-card">
              <strong>上传或粘贴简历</strong>
              <p>支持文本输入，也支持 TXT / PDF 文件解析。</p>
            </article>
            <article class="feature-card">
              <strong>逐步分析匹配度</strong>
              <p>展示岗位亮点、能力缺口和针对性优化建议。</p>
            </article>
            <article class="feature-card">
              <strong>生成最终简历成品</strong>
              <p>输出中文成品简历，并保留 Markdown 原文便于继续修改。</p>
            </article>
          </div>
        </section>
      </main>
    </template>

    <template v-else>
      <main class="flow-layout">
        <aside class="flow-sidebar card">
          <div class="sidebar-top">
            <p class="eyebrow">功能流程</p>
            <h2>简历优化</h2>
            <p>每个阶段独立展示，结果确认后再进入下一步。</p>
          </div>

          <div class="step-list">
            <button
              v-for="(step, index) in steps"
              :key="step.key"
              class="step-item"
              :class="{
                active: currentStepIndex === index,
                done:
                  (step.key === 'resume' && canContinueResume) ||
                  (step.key === 'jd' && canAnalyze) ||
                  (step.key === 'analysis' && analysis) ||
                  (step.key === 'result' && optimized),
              }"
              @click="goToStep(step.key)"
            >
              <span>{{ step.number }}</span>
              <div>
                <strong>{{ step.title }}</strong>
              </div>
            </button>
          </div>

          <button class="ghost-button" @click="restartFlow">返回首页</button>
        </aside>

        <section class="page-card card">
          <p v-if="errorMessage" class="error-banner">{{ errorMessage }}</p>

          <template v-if="page === 'resume'">
            <div class="page-head">
              <p class="section-kicker">步骤一</p>
              <h1>输入原始简历</h1>
              <p>请粘贴简历内容，或上传 TXT / PDF 文件。内容越完整，后续分析越准确。</p>
            </div>

            <div class="tool-row">
              <label class="upload-button">
                <span>{{ uploadLoading ? "正在解析..." : "上传 TXT / PDF" }}</span>
                <input type="file" accept=".txt,.pdf,text/plain,application/pdf" @change="handleFileUpload" />
              </label>
              <span v-if="uploadedFilename" class="tag">已解析：{{ uploadedFilename }}</span>
            </div>

            <textarea
              v-model="resumeText"
              class="text-area large-area"
              placeholder="请输入或粘贴简历内容。"
              @input="resetResults"
            />

            <div class="page-actions">
              <button class="primary-button" :disabled="!canContinueResume" @click="page = 'jd'">下一步：输入目标职位</button>
            </div>
          </template>

          <template v-else-if="page === 'jd'">
            <div class="page-head">
              <p class="section-kicker">步骤二</p>
              <h1>输入目标职位描述</h1>
              <p>请输入岗位职责、技术要求、经验要求和加分项，系统会据此分析简历匹配度。</p>
            </div>

            <textarea
              v-model="jobDescription"
              class="text-area large-area"
              placeholder="请输入目标岗位 JD。"
              @input="resetResults"
            />

            <div class="page-actions split">
              <button class="secondary-button" @click="page = 'resume'">上一步</button>
              <button class="primary-button" :disabled="!canAnalyze || loadingAnalysis" @click="analyzeMatch">
                开始分析
              </button>
            </div>
          </template>

          <template v-else-if="page === 'analyzing' || page === 'optimizing'">
            <div class="waiting-screen">
              <div class="loader-ring"></div>
              <p class="section-kicker">处理中</p>
              <h1>{{ waitingTitle }}</h1>
              <p>{{ waitingDescription }}</p>

              <div class="progress-block">
                <div class="progress-track">
                  <div class="progress-bar"></div>
                </div>
                <div class="progress-meta">
                  <span>请稍候，结果将在当前页面自动展示</span>
                  <span>{{ page === "analyzing" ? "分析阶段" : "生成阶段" }}</span>
                </div>
              </div>
            </div>
          </template>

          <template v-else-if="page === 'analysis'">
            <div class="page-head">
              <p class="section-kicker">步骤三</p>
              <h1>查看匹配分析结果</h1>
              <p>先确认亮点、缺口和修改建议，再决定是否生成优化后的简历成品。</p>
            </div>

            <div class="score-panel">
              <span>匹配度评分</span>
              <strong>{{ analysis.match_score }}</strong>
              <p>{{ analysis.analysis_summary }}</p>
            </div>

            <div class="analysis-grid">
              <article class="info-card">
                <h3>匹配亮点</h3>
                <ul>
                  <li v-for="item in analysis.strengths" :key="item">{{ item }}</li>
                </ul>
              </article>
              <article class="info-card">
                <h3>主要缺口</h3>
                <ul>
                  <li v-for="item in analysis.gaps" :key="item">{{ item }}</li>
                </ul>
              </article>
              <article class="info-card full">
                <h3>优化建议</h3>
                <ul>
                  <li v-for="item in analysis.suggestions" :key="item">{{ item }}</li>
                </ul>
              </article>
            </div>

            <div class="page-actions split">
              <button class="secondary-button" @click="page = 'jd'">返回修改 JD</button>
              <button class="primary-button" :disabled="loadingOptimization" @click="generateOptimizedResume">
                生成优化后的简历
              </button>
            </div>
          </template>

          <template v-else-if="page === 'result'">
            <div class="page-head">
              <p class="section-kicker">步骤四</p>
              <h1>优化后的简历成品</h1>
              <p>这里展示最终成品预览，同时保留 Markdown 原文，方便继续微调和导出。</p>
            </div>

            <div class="page-actions split compact-top">
              <button class="secondary-button" @click="page = 'analysis'">返回分析结果</button>
              <div class="button-row">
                <button class="secondary-button" @click="exportMarkdown">导出 .md</button>
                <button class="secondary-button" @click="exportTxt">导出 .txt</button>
              </div>
            </div>

            <div class="result-grid">
              <article class="info-card full">
                <h3>本次改写重点</h3>
                <ul>
                  <li v-for="item in optimized.change_summary" :key="item">{{ item }}</li>
                </ul>
              </article>

              <article class="resume-preview">
                <div class="resume-preview-head">
                  <h3>最终简历预览</h3>
                  <span>可直接查看的成品版式</span>
                </div>
                <div class="resume-document" v-html="renderedResumeHtml"></div>
              </article>

              <article class="info-card full">
                <h3>Markdown 原文</h3>
                <pre class="source-pre">{{ optimized.optimized_resume_markdown }}</pre>
              </article>
            </div>
          </template>
        </section>
      </main>
    </template>
  </div>
</template>
