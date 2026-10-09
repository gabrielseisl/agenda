const $ = (s) => document.querySelector(s);

/* ---------- login obrigatório ao recarregar / voltar ---------- */
const _nav = performance.getEntriesByType("navigation")[0];
const FORCAR_LOGIN = !!_nav && (_nav.type === "reload" || _nav.type === "back_forward");

async function encerrarSessao() {
  try { await fetch("/api/auth/sair", { method: "POST", keepalive: true }); } catch {}
  window.location.replace("/login");
}

if (FORCAR_LOGIN) {
  encerrarSessao();                       // recarregou ou voltou: pede login de novo
} else {
  document.documentElement.classList.remove("verificando");
}
// Voltou por cache do navegador (seta de voltar)
window.addEventListener("pageshow", (e) => {
  if (e.persisted) {
    document.documentElement.classList.add("verificando");
    encerrarSessao();
  }
});
// O login é encerrado explicitamente ao recarregar/voltar ou ao clicar em Sair.
 // Evita enviar um logout assíncrono em navegações normais e causar corrida com o login.

const PRIO_ROTULO = { alta: "Alta", media: "Média", baixa: "Baixa" };

let dataAtual = fmtData(new Date());
let atividades = [];
let editandoId = null;

/* ---------- utilidades ---------- */
function fmtData(d) {
  const p = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`;
}
function somarDias(str, n) {
  const [y, m, d] = str.split("-").map(Number);
  return fmtData(new Date(y, m - 1, d + n));
}
function fmtDuracao(min) {
  const h = Math.floor(min / 60), m = min % 60;
  if (!h) return `${m}min`;
  return m ? `${h}h${String(m).padStart(2, "0")}` : `${h}h`;
}
function paraMin(hhmm) {
  const [h, m] = hhmm.split(":").map(Number);
  return h * 60 + m;
}
function deMin(total) {
  const p = (n) => String(n).padStart(2, "0");
  return `${p(Math.floor(total / 60) % 24)}:${p(total % 60)}`;
}
function avisar(msg, erro = false) {
  const t = $("#toast");
  t.textContent = msg;
  t.className = "toast" + (erro ? " erro" : "");
  t.hidden = false;
  clearTimeout(avisar.timer);
  avisar.timer = setTimeout(() => (t.hidden = true), 3500);
}
async function api(url, opcoes = {}) {
  let resp;
  try {
    resp = await fetch(url, { headers: { "Content-Type": "application/json" }, ...opcoes });
  } catch {
    throw new Error("Não foi possível falar com o servidor.");
  }
  if (resp.status === 401) {
    window.location.href = "/login";
    throw new Error("Sessão expirada. Entre novamente.");
  }
  if (!resp.ok) {
    let msg = `Erro ${resp.status}`;
    if (resp.status >= 500) msg = "Erro no servidor. Verifique se o MySQL está ligado e se o .env está correto.";
    try {
      const j = await resp.json();
      if (typeof j.detail === "string") msg = j.detail;
      else if (Array.isArray(j.detail)) msg = j.detail.map((e) => e.msg).join("; ");
    } catch {}
    throw new Error(msg);
  }
  return resp.status === 204 ? null : resp.json();
}

/* ---------- carregar e desenhar ---------- */
async function carregar() {
  $("#data").value = dataAtual;
  const d = new Date(dataAtual + "T00:00:00");
  $("#dia-numero").textContent = d.getDate();
  $("#dia-semana").textContent = d.toLocaleDateString("pt-BR", { weekday: "long" });
  $("#dia-mes").textContent = d.toLocaleDateString("pt-BR", { month: "long", year: "numeric" });
  try {
    atividades = await api(`/api/atividades?data=${dataAtual}`);
  } catch (e) {
    atividades = [];
    avisar(e.message, true);
  }
  desenhar();
}

function detectarConflitos() {
  const conflitos = new Set();
  const comHorario = atividades
    .filter((a) => a.horario)
    .map((a) => ({ id: a.id, ini: paraMin(a.horario), fim: paraMin(a.horario) + a.duracao_min }))
    .sort((a, b) => a.ini - b.ini);
  let fimAnterior = -1, idAnterior = null;
  for (const a of comHorario) {
    if (a.ini < fimAnterior) { conflitos.add(a.id); conflitos.add(idAnterior); }
    if (a.fim > fimAnterior) { fimAnterior = a.fim; idAnterior = a.id; }
  }
  return conflitos;
}

function desenhar() {
  const lista = $("#lista");
  lista.innerHTML = "";
  $("#vazio").hidden = atividades.length > 0;
  const n = atividades.length;
  $("#contador").textContent = n ? `${n} ${n === 1 ? "atividade" : "atividades"}` : "";
  const conflitos = detectarConflitos();

  for (const a of atividades) {
    const li = document.createElement("li");
    li.className = `item${a.concluida ? " feita" : ""}`;

    const chk = document.createElement("input");
    chk.type = "checkbox";
    chk.checked = a.concluida;
    chk.title = "Marcar como concluída";
    chk.addEventListener("change", () => alternar(a.id));

    const hora = document.createElement("div");
    hora.className = "hora";
    if (a.horario) {
      const ini = a.horario.slice(0, 5);
      hora.textContent = ini;
      const fim = document.createElement("small");
      fim.textContent = "até " + deMin(paraMin(ini) + a.duracao_min);
      hora.appendChild(fim);
    } else {
      hora.classList.add("sem");
      hora.textContent = "Sem horário";
    }

    const info = document.createElement("div");
    info.className = "info";
    const titulo = document.createElement("div");
    titulo.className = "titulo-item";
    titulo.textContent = a.titulo;
    const meta = document.createElement("div");
    meta.className = "meta";
    meta.textContent = "Duração: " + fmtDuracao(a.duracao_min);
    if (conflitos.has(a.id)) {
      const c = document.createElement("span");
      c.className = "conflito";
      c.textContent = "Conflito de horário";
      meta.appendChild(c);
    }
    info.append(titulo, meta);

    const prio = document.createElement("span");
    prio.className = `prio ${a.prioridade}`;
    prio.textContent = PRIO_ROTULO[a.prioridade];

    const botoes = document.createElement("div");
    botoes.className = "botoes";
    const bEd = document.createElement("button");
    bEd.textContent = "Editar";
    bEd.addEventListener("click", () => iniciarEdicao(a));
    const bEx = document.createElement("button");
    bEx.textContent = "Excluir";
    bEx.className = "excluir";
    bEx.addEventListener("click", () => excluir(a.id));
    botoes.append(bEd, bEx);

    li.append(chk, hora, info, prio, botoes);
    lista.appendChild(li);
  }
  atualizarResumo();
}

function atualizarResumo() {
  const horas = parseFloat($("#horas").value) || 0;
  const disponivel = Math.round(horas * 60);
  const planejado = atividades.reduce((s, a) => s + a.duracao_min, 0);
  const feito = atividades.filter((a) => a.concluida).reduce((s, a) => s + a.duracao_min, 0);
  const livre = disponivel - planejado;

  $("#st-planejado").textContent = fmtDuracao(planejado);
  $("#st-feito").textContent = fmtDuracao(feito);
  $("#st-livre").textContent = (livre < 0 ? "-" : "") + fmtDuracao(Math.abs(livre));

  const pct = disponivel > 0 ? Math.min(100, (planejado / disponivel) * 100) : 100;
  const barra = $("#barra-preench");
  barra.style.width = pct + "%";
  barra.className = "barra-preench" + (planejado > disponivel ? " estourou" : pct >= 85 ? " alerta" : "");

  const aviso = $("#aviso");
  if (!atividades.length) {
    aviso.textContent = "";
    aviso.className = "aviso";
  } else if (livre < 0) {
    aviso.textContent = `Não cabe no dia: faltam ${fmtDuracao(-livre)}. Reduza ou mova atividades de baixa prioridade.`;
    aviso.className = "aviso erro";
  } else if (livre < 30) {
    aviso.textContent = `Dia quase cheio: sobram apenas ${fmtDuracao(livre)}.`;
    aviso.className = "aviso alerta";
  } else {
    aviso.textContent = `Cabe no dia. Sobram ${fmtDuracao(livre)}.`;
    aviso.className = "aviso ok";
  }
}

/* ---------- ações ---------- */
function limparForm() {
  editandoId = null;
  $("#form").reset();
  $("#duracao").value = 30;
  $("#prioridade").value = "media";
  $("#titulo-form").textContent = "Nova atividade";
  $("#btn-salvar").textContent = "Adicionar";
  $("#btn-cancelar").hidden = true;
}

function iniciarEdicao(a) {
  editandoId = a.id;
  $("#titulo").value = a.titulo;
  $("#horario").value = a.horario ? a.horario.slice(0, 5) : "";
  $("#duracao").value = a.duracao_min;
  $("#prioridade").value = a.prioridade;
  $("#titulo-form").textContent = "Editar atividade";
  $("#btn-salvar").textContent = "Salvar";
  $("#btn-cancelar").hidden = false;
  $("#titulo").focus();
  $("#form").scrollIntoView({ behavior: "smooth", block: "center" });
}

async function salvar(ev) {
  ev.preventDefault();
  const corpo = {
    titulo: $("#titulo").value.trim(),
    data: dataAtual,
    horario: $("#horario").value || null,
    duracao_min: parseInt($("#duracao").value, 10) || 30,
    prioridade: $("#prioridade").value,
  };
  try {
    if (editandoId) {
      await api(`/api/atividades/${editandoId}`, { method: "PUT", body: JSON.stringify(corpo) });
      avisar("Atividade atualizada.");
    } else {
      await api("/api/atividades", { method: "POST", body: JSON.stringify(corpo) });
      avisar("Atividade adicionada.");
    }
    limparForm();
    await carregarUsuario();
carregar();
  } catch (e) {
    avisar(e.message, true);
  }
}

async function alternar(id) {
  try {
    await api(`/api/atividades/${id}/concluir`, { method: "PATCH" });
    await carregarUsuario();
carregar();
  } catch (e) {
    avisar(e.message, true);
  }
}

async function excluir(id) {
  if (!confirm("Excluir esta atividade?")) return;
  try {
    await api(`/api/atividades/${id}`, { method: "DELETE" });
    if (editandoId === id) limparForm();
    await carregarUsuario();
carregar();
  } catch (e) {
    avisar(e.message, true);
  }
}

async function carregarUsuario() {
  try {
    const u = await api("/api/auth/eu");
    $("#usuario-nome").textContent = u.nome;
  } catch {}
}

function sair() {
  encerrarSessao();
}

/* ---------- eventos ---------- */
$("#btn-sair").addEventListener("click", sair);
$("#form").addEventListener("submit", salvar);
$("#btn-cancelar").addEventListener("click", limparForm);
$("#btn-ontem").addEventListener("click", () => { dataAtual = somarDias(dataAtual, -1); carregar(); });
$("#btn-amanha").addEventListener("click", () => { dataAtual = somarDias(dataAtual, 1); carregar(); });
$("#btn-hoje").addEventListener("click", () => { dataAtual = fmtData(new Date()); carregar(); });
$("#data").addEventListener("change", (e) => { if (e.target.value) { dataAtual = e.target.value; carregar(); } });
$("#horas").addEventListener("input", () => {
  try { localStorage.setItem("meudia_horas", $("#horas").value); } catch {}
  atualizarResumo();
});

try {
  const salvo = localStorage.getItem("meudia_horas");
  if (salvo) $("#horas").value = salvo;
} catch {}
if (!FORCAR_LOGIN) {
  carregarUsuario();
  carregar();
}
